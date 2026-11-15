"""Generate attribution-rich, source-backed scientific PDF reports."""
from __future__ import annotations

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

NAVY=HexColor('#0B1823'); TEAL=HexColor('#087B6F'); DARK=HexColor('#1B303E'); GREY=HexColor('#526676')


def _text(c, x, y, s, size=10, color=DARK, font='Helvetica'):
    c.setFont(font,size);c.setFillColor(color);c.drawString(x,y,str(s))


def build_pdf_report(result: dict, place_name: str = 'Selected point') -> bytes:
    """Create a self-contained 2-page PDF from a validated investigation result."""
    buffer=BytesIO();c=canvas.Canvas(buffer, pagesize=A4)
    W,H=A4;left=50;right=W-50
    d=result;trend=d['trend'];annual=d['annual'];source=d['evidence'];var=d['variable']
    c.setTitle(f'AETHERIS Scientific Investigation - {place_name}')
    c.setAuthor('AETHERIS | Independent Scientific Research Software')
    c.setFillColor(NAVY);c.rect(0,H-145,W,145,stroke=0,fill=1)
    _text(c,left,H-51,'A E T H E R I S',20,HexColor('#BDF2E6'),'Helvetica-Bold')
    _text(c,left,H-73,'SCIENTIFIC INVESTIGATION REPORT  /  01',9,HexColor('#7FADB0'))
    _text(c,left,H-113,place_name[:60],15,HexColor('#FFFFFF'),'Helvetica-Bold')
    _text(c,left,H-171,f"{var['label']}  |  {trend['start_year']}-{trend['end_year']}  |  {source.get('provider','Data provider')[:28]}",12,DARK,'Helvetica-Bold')
    _text(c,left,H-192,f"Coordinates: {d['location']['latitude']:.4f}, {d['location']['longitude']:.4f}  |  Complete years: {trend['sample_size']}",9,GREY)
    y=H-223
    kpis=[('ESTIMATED CHANGE',f"{trend['slope_per_decade']:+.3f} {trend['slope_unit']}"),('HAC P-VALUE', ('<0.00001' if trend['p_value_hac'] < .00001 else f"{trend['p_value_hac']:.5f}") if trend['p_value_hac'] is not None else 'Unavailable'),('EVIDENCE',trend['significance_label'].title())]
    width=(W-2*left-16)/3
    for idx,(lab,value) in enumerate(kpis):
        x=left+idx*(width+8);c.setFillColor(HexColor('#EAF3F1'));c.roundRect(x,y-51,width,55,6,stroke=0,fill=1)
        _text(c,x+10,y-15,lab,8,TEAL,'Helvetica-Bold')
        # shrink long values to prevent overflow
        size=12 if len(value)<19 else 9
        _text(c,x+10,y-35,value,size,DARK,'Helvetica-Bold')
    cy=y-88
    _text(c,left,cy,'ANNUAL OBSERVATIONS AND FITTED LINE',11,DARK,'Helvetica-Bold')
    x0,x1=left+28,right-9;yb=cy-219;yt=cy-30
    vals=[float(p['value']) for p in annual]+[float(p['value']) for p in trend['fitted']]
    low,high=min(vals),max(vals);rng=(high-low) or 1;low-=.12*rng;high+=.12*rng
    yr0,yr1=annual[0]['year'],annual[-1]['year'];yrange=(yr1-yr0) or 1
    XX=lambda yr:x0+(yr-yr0)/yrange*(x1-x0)
    YY=lambda val:yb+(val-low)/(high-low)*(yt-yb)
    for i in range(5):
        val=low+(high-low)*i/4;Y=YY(val)
        c.setStrokeColor(HexColor('#DDE6E8'));c.setLineWidth(.6);c.line(x0,Y,x1,Y)
        _text(c,left-5,Y-3,f'{val:.1f}',8,GREY)
    for idx, (pts, color, linewidth) in enumerate([(annual, TEAL, 1.9),(trend['fitted'],HexColor('#E38E48'),2)]):
        c.setStrokeColor(color);c.setLineWidth(linewidth)
        p=c.beginPath()
        for j,v in enumerate(pts):
            x=XX(v['year']);Y=YY(v['value'])
            if j==0:p.moveTo(x,Y)
            else:p.lineTo(x,Y)
        c.drawPath(p)
    for yr in [yr0,(yr0+yr1)//2,yr1]:_text(c,XX(yr)-14,yb-16,yr,8,GREY)
    _text(c,left,yb-40,'Teal: annual values       Orange: OLS fitted trend',9,GREY)
    _text(c,left,yb-69,'SCIENTIFIC INTERPRETATION',11,DARK,'Helvetica-Bold')
    _text(c,left,yb-87,f"Slope: {trend['slope_per_decade']:+.4f} {trend['slope_unit']}; Theil-Sen: {trend['theil_sen_per_decade']:+.4f} {trend['slope_unit']}",9,DARK)
    ci=trend.get('ci95_hac_per_decade')
    if ci:_text(c,left,yb-104,f"Exploratory HAC 95% CI: [{ci[0]:.4f}, {ci[1]:.4f}] {trend['slope_unit']}",9,DARK)
    _text(c,left,56,'Independent research software. Not NASA-endorsed. See methodology and limitations on page 2.',8,GREY)
    _text(c,right-55,36,'PAGE 01 / 02',8,GREY)
    c.showPage()
    # PAGE 2
    c.setFillColor(NAVY);c.rect(0,H-100,W,100,stroke=0,fill=1)
    _text(c,left,H-50,'EVIDENCE & METHODOLOGY',18,HexColor('#C0EFE5'),'Helvetica-Bold')
    y=H-130
    entries=[('Source',source.get('provider','NASA POWER')),('Product',source.get('product','')),('Period',f"{trend['start_year']}-{trend['end_year']}"),('Variable',f"{var['id']} ({trend['annual_unit']})"),('Aggregation',source.get('annual_aggregation','')),('Statistical method',source.get('science_method','')),('Data SHA-256',source.get('sha256_monthly','')),('Request',source.get('source_request','')),('Generated UTC',d.get('generated_at',''))]
    for label,value in entries:
        _text(c,left,y,label.upper(),8,TEAL,'Helvetica-Bold')
        # split and wrap with no external font dependency
        value=str(value)
        segments=[value[i:i+88] for i in range(0,len(value),88)] or ['']
        for j,seg in enumerate(segments[:3]):_text(c,left+110,y-j*14,seg,8,DARK)
        y-=max(27,len(segments[:3])*14+9)
    _text(c,left,y-4,'LIMITATIONS',11,DARK,'Helvetica-Bold');y-=28
    for limitation in d.get('limitations',[])[:7]:
        clean=limitation.replace('–','-').replace('°','deg').replace('’',"'")
        words=clean.split();lines=[];current=''
        for word in words:
            if len(current)+len(word)>95:lines.append(current);current=word
            else:current=(current+' '+word).strip()
        if current:lines.append(current)
        for part in lines[:3]:_text(c,left+8,y,'- '+part,8,GREY);y-=12
        y-=8
        if y<83:break
    _text(c,left,48,'POWER: https://power.larc.nasa.gov/  |  Research interpretations require domain review.',8,GREY)
    _text(c,right-55,30,'PAGE 02 / 02',8,GREY)
    c.save();return buffer.getvalue()

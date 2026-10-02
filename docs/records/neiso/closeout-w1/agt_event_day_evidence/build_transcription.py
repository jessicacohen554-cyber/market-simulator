"""closeout-NEISO wave 1: rebuild agt_event_day_evidence/transcription.csv from the saved source files (PDFs/HTML not committed; SHA256SUMS lists them)."""
import csv,re,subprocess,glob,datetime as dt
rows=[]
H=['date','usd_mmbtu','kind','date_basis','span_start','span_end','source_title','url','page','quote']
def add(**k): rows.append([k.get(h,'') for h in H])
NG='EIA Natural Gas Weekly Update (prices: NGI via Bloomberg)'
add(date='2022-01-25',usd_mmbtu='24.62',kind='weekly_high',date_basis='unspecified',span_start='2022-01-20',span_end='2022-01-26',source_title=NG+', release 2022-01-27',url='https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2022/01_27/',page='html',quote='At the Algonquin Citygate, which serves Boston-area consumers , the price went down $1.98 from $22.69/MMBtu last Wednesday to $20.71/MMBtu yesterday, after reaching a daily high for the week of $24.62/MMBtu on Tuesday.')
add(date='',usd_mmbtu='26.94',kind='weekly_high',date_basis='unspecified',span_start='2022-01-13',span_end='2022-01-19',source_title=NG+', release 2022-01-20',url='https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2022/01_20/',page='html',quote='Prices at the Algonquin Citygate rose to a weekly high of $26.94/MMBtu in advance of the holiday weekend, when temperatures were expected to drop significantly.')
add(date='2023-02-02',usd_mmbtu='71.42',kind='daily',date_basis='unspecified',span_start='2023-02-02',span_end='2023-02-02',source_title=NG+', release 2023-02-09',url='https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2023/02_09/',page='html',quote='Last Thursday, February 2, the price at Algonquin Citygate spiked to $71.42/MMBtu, the highest daily price since January 4, 2018, when it reached $78.98/MMBtu.')
add(date='',usd_mmbtu='6.75',kind='weekly_high',date_basis='unspecified',span_start='2025-06-19',span_end='2025-06-25',source_title=NG+', release 2025-06-26',url='https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/2025/06_26/',page='html',quote='In the Northeast, prices at the Algonquin Citygate, a natural gas benchmark price covering Boston-area consumers , fell 89 cents from $3.50/MMBtu last Wednesday to $2.61/MMBtu yesterday, after reaching a mid-week high of $6.75/MMBtu.')
TIE='EIA Today in Energy: New England natural gas and electricity prices increase on supply constraints, high demand (id=51158; data NGI)'
add(date='',usd_mmbtu='20.55',kind='multi_day_average',date_basis='unspecified',span_start='2022-01-01',span_end='2022-01-31',source_title=TIE,url='https://www.eia.gov/todayinenergy/detail.php?id=51158',page='html',quote='The spot natural gas price at the Algonquin Citygate, a trading hub and the benchmark for the natural gas price in New England, averaged $20.55 per million British thermal units (MMBtu) during January 2022')
COMP=' -- NOT Algonquin-only: ISO-NE IMM weighted average of ICE next-day indices (Algonquin Citygates, Algonquin Non-G, Portland, TGP Z6-200L%s)'
AMR='ISO-NE IMM 2022 Annual Markets Report'+COMP%(', TGP North, TGP South, Maritimes & Northeast')
u='https://www.iso-ne.com/static-assets/documents/2023/06/2022-annual-markets-report.pdf'
add(date='',usd_mmbtu='35.37',kind='multi_day_average',date_basis='unspecified',span_start='2022-12-24',span_end='2022-12-27',source_title=AMR,url=u,page='PDF 36 / printed 29 (also PDF 17 / printed 10)',quote='A cold snap affected New England from December 24 to December 27 and led to an average daily natural gas price of $35.37/MMBtu over the four days, the highest daily averages since Q4 2018.')
Q='ISO-NE IMM Winter 2023 Quarterly Markets Report'+COMP%''
u='https://www.iso-ne.com/static-assets/documents/2023/05/2023-winter-quarterly-markets-report.pdf'
add(date='2022-12-22',usd_mmbtu='6.66',kind='daily',date_basis='flow',span_start='2022-12-22',span_end='2022-12-22',source_title=Q,url=u,page='PDF 31 / printed 29',quote='Oil-fired generation began clearing more energy in the day-ahead market beginning at HE 11 on December 23 when the average hourly gas price rose from $6.66/MMBtu to $30.05/MMBtu. [hourly series; value in force before HE11 Dec 23 = gas day Dec 22 per fn 4 gas-day definition]')
add(date='2022-12-23',usd_mmbtu='30.05',kind='daily',date_basis='flow',span_start='2022-12-23',span_end='2022-12-23',source_title=Q,url=u,page='PDF 31 / printed 29',quote='Oil-fired generation began clearing more energy in the day-ahead market beginning at HE 11 on December 23 when the average hourly gas price rose from $6.66/MMBtu to $30.05/MMBtu. [value from HE11 Dec 23 = gas day Dec 23]')
add(date='2022-12-24',usd_mmbtu='35.99',kind='daily',date_basis='unspecified',span_start='2022-12-24',span_end='2022-12-24',source_title=Q,url=u,page='PDF 31 / printed 29',quote='Gas prices continued their upward climb on December 24, rising to an average system gas price of $35.99/MMBtu.')
add(date='2023-02-03',usd_mmbtu='76.42',kind='daily',date_basis='flow',span_start='2023-02-03',span_end='2023-02-03',source_title=Q,url=u,page='PDF 41 / printed 39',quote='In response to the extreme cold weather experienced during this period, the average price of gas in New England soared to $76.42/MMBtu for the February 3 gas day.')
Q2='ISO-NE IMM Winter 2022 Quarterly Markets Report'+COMP%''
add(date='',usd_mmbtu='22.99',kind='multi_day_average',date_basis='unspecified',span_start='2022-01-08',span_end='2022-01-31',source_title=Q2,url='https://www.iso-ne.com/static-assets/documents/2022/05/2022-winter-quarterly-markets-report.pdf',page='PDF 22 / printed 15',quote='From January 8 – January 31, temperatures averaged 22⁰F ... During this cold spell, natural gas prices averaged $22.99/MMBtu compared to $11.29/MMBtu throughout the rest of Winter 2022')
# dashboard
for f in sorted(glob.glob('dash/2*.pdf')):
  t=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
  pages=t.split('\f')
  for i,p in enumerate(pages):
    if '(Algonquin Citygate)' in p and 'Spot natural gas price' in p and 'This indicator' not in p:
      mv=re.search(r'Bcf/d\s+(-?[\d.]+|--) \$/MMBtu',p)
      ml=re.search(r'\(Algonquin Citygate\)\s*\n(?:.*\n){0,3}?.*?(\d+/\d+/\d+)\s*$',p,re.M)
      if mv and mv.group(1)!='--':
        lab=ml.group(1); d=dt.datetime.strptime(lab,'%m/%d/%y').date().isoformat()
        upd=re.search(r'Last daily update: (.*?) Next',t).group(1)
        fn=f.split('/')[-1]
        add(date=d,usd_mmbtu=mv.group(1),kind='daily',date_basis='unspecified',span_start=d,span_end=d,source_title=f'EIA New England Dashboard archive snapshot (last daily update {upd}); price source S&P Global Market Intelligence',url=f'https://www.eia.gov/dashboard/new-england-energy-api/archives/{fn[:6]}/{fn[:8]}_new_england_dashboard.pdf',page=f'PDF {i+1} (no printed page no.)',quote=f'{mv.group(1)} $/MMBtu | Spot natural gas price (Algonquin Citygate) {lab}')
      break
with open('transcription.csv','w',newline='') as fh:
  w=csv.writer(fh); w.writerow(H); w.writerows(rows)
print(len(rows))

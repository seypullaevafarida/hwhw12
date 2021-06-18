from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import random
from bs4 import BeautifulSoup
import numpy as np
from requests import get
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
def torus(x):
  if x is not np.nan:
    try:
      return x.strip().encode('l1').decode()
    except:
      return x
  return x
def dropndg(x):
  s = ''
  for a in x:
    if a.isdigit() or a == '.':
      s += a
  return float(s)
TOKEN = '1876387848:AAFf82dRxMAzH1F_3gTxDtjpiI4Arr3SKGU'
dct_type = {'h':'Высота', 
            's':'Автономное сохранение холода', 
            'v':'Общий объем',
            'w':'Мощность замораживания'}
all=[]
for i in range(20):
  request=get('https://tehnobt.ru/catalog/krupnaya_bytovaya_tekhnika/kholodilniki_i_morozilniki/?PAGEN_4={0}'.format(i+1))
  html=BeautifulSoup(request.text,'lxml')
  html=html.find('div',class_='items productList')
  holodilniks=html.find_all('div',class_='productColText')
  for obj in holodilniks:
    name=obj.find('a',class_='name')
    href=name['href']
    name=name.text
    price=obj.find('a',class_='price').text
    all.append([name,href,price]+[np.nan for j in range(23)])
first=BeautifulSoup(get('https://tehnobt.ru/catalog/krupnaya_bytovaya_tekhnika/kholodilniki_i_morozilniki/kholodilniki_side_by_side/kholodilnik_hiberg_rfq_490dx_nfgw.html').text,'lxml')
table=first.find('table',class_='stats').find_all('tr')[1:]
stats=[]
for t in table:
  stats.append(t.find('td',class_='name').text)
for j in range(len(all)):
  href='https://tehnobt.ru'+all[j][1]
  obj=BeautifulSoup(get(href).text,'lxml')
  table=obj.find('table',class_='stats').find_all('tr')[1:]
  for t in table:
    name=t.find('td',class_='name').text
    try:
      if name.encode('l1').decode() in stats:
        index=stats.index(name.encode('l1').decode())+3
        all[j][index]=t.find_all('td')[1].text
    except:
      if name in stats:
        index=stats.index(name)+3
        all[j][index]=t.find_all('td')[1].text
al=pd.DataFrame(all,columns=['Название','Ссылка','Цена']+[x for x in stats])
for col in al.columns[4:]:
  al[col]=al[col].apply(torus)
al['Цена']=al['Цена'].apply(lambda x:x.replace('\t','').strip())
al = al[['Цена', 'Производитель', 'Автономное сохранение холода', 'Высота', 'Общий объем', 'Мощность замораживания']]
al['Цена'] = al['Цена'].apply(lambda x:int(''.join(x.split('руб')[0].split())))
al = al.dropna()
for x in ['Автономное сохранение холода', 'Высота', 'Общий объем', 'Мощность замораживания']:
  al[x] = al[x].apply(dropndg)
data = al
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
keyboard = InlineKeyboardMarkup()
b1 = InlineKeyboardButton('Производитель', callback_data='Cp')
b21 = InlineKeyboardButton('Высота', callback_data='Ch')
b22 = InlineKeyboardButton('Автономное сохранение холода', callback_data='Cs')
b31 = InlineKeyboardButton('Общий объем', callback_data='Cv')
b32 = InlineKeyboardButton('Мощность замораживания', callback_data='Cw')
b4 = InlineKeyboardButton('Построить матрицу корреляций', callback_data='corr')
b5 = InlineKeyboardButton('Посчитать статистики для цены и построить boxplot', callback_data='stat')
pcount = {}
for x in data['Производитель'].unique():
    pcount[x] = (data['Производитель'] == x).sum()
keyboard.add(b1)
keyboard.row(b21, b22)
keyboard.row(b31, b32)
keyboard.add(b4)
keyboard.add(b5)
@dp.message_handler(commands=['start'])
async def welcome(msg: types.Message):
    await msg.reply('Привет! Я холодильникбот, эксперт по холодильникам. Вы можете выбрать критерий разбиения данных и я дам аналитику по ценам:',
                    reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data and call.data.startswith('C'))
async def callback(msg: types.CallbackQuery):
    if msg.data[1] == 'p':
        await handle_p(msg)
    else:
        await handle_chisl(msg, msg.data[1])

@dp.callback_query_handler(lambda call:call.data and call.data.startswith('s'))
async def stat(msg: types.CallbackQuery):
    mean = data['Цена'].mean()
    std = data['Цена'].std()
    disp = std ** 2
    graph = sns.boxplot(x=data['Цена']).get_figure()
    graph.savefig('box.png')
    plt.close()
    with open('box.png', 'rb') as photo:
        await bot.send_photo(msg.from_user.id, photo, caption=f'Среднее:{mean} \nСтандартное отклонение:{std} \nДисперсия:{disp})')
    await bot.send_message(msg.from_user.id, 'Желаете ещё аналитику?', reply_markup=keyboard)
    

@dp.callback_query_handler(lambda call: call.data and call.data.startswith('corr'))
async def corr(msg: types.CallbackQuery):
    new_data = data.drop('Производитель', axis=1)
    graph = sns.heatmap(new_data.corr(), cmap='coolwarm', annot=True, 
                        xticklabels = new_data.columns, yticklabels = new_data.columns).get_figure()
    graph.savefig('corr.png')
    plt.close()
    with open('corr.png', 'rb') as photo:
        await bot.send_photo(msg.from_user.id, photo, caption='Матрица корреляций между различными признаками')
    await bot.send_message(msg.from_user.id, 'Желаете ещё аналитику?', reply_markup=keyboard)

async def handle_p(msg):
    await bot.send_message(msg.from_user.id, 'Группировка по средней цене у различных производителей:')
    graph = data[data['Производитель'].apply(lambda x:pcount[x]) >= 3].groupby('Производитель')['Цена'].mean().plot(kind='pie')
    graph.get_figure().savefig('proizv.png')
    plt.close()
    with open('proizv.png', 'rb') as photo:
        await bot.send_photo(msg.from_user.id, photo)
    await bot.send_message(msg.from_user.id, 'Желаете ещё аналитику?', reply_markup=keyboard)

async def handle_chisl(msg, typ):
    col = dct_type[typ]
    corr = data[['Цена', col]].corr()['Цена'].loc[col]
    await bot.send_message(msg.from_user.id, f'Коэффициент корреляции между ценой и признаком "{col}" равен: {corr}. Сейчас будет график:')
    graph = sns.jointplot(x='Цена', y=col, data=data[['Цена', col]], kind='reg', dropna=True)
    graph.plot_joint(sns.kdeplot, color='g')
    graph.savefig(f'{col}.png')
    plt.close()
    if corr < -0.3:
        txt = 'Признаки сильно связаны, корреляция имеет отрицательный характер'
    if corr > 0.3:
        txt = 'Признаки сильно связаны, корреляция имеет положительный характер'
    else:
        txt = 'Признаки слабо связаны,'
        if corr > 0:
            txt += 'корреляция имеет положительный характер'
        else:
            txt += 'корреляция имеет отрицательный характер'
    with open(f'{col}.png', 'rb') as photo:
        await bot.send_photo(msg.from_user.id, photo, caption=txt)
    await bot.send_message(msg.from_user.id, 'Желаете ещё аналитику?', reply_markup=keyboard)
        
if __name__=='__main__':
    executor.start_polling(dp)

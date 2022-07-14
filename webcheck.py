import requests

url = input('Escriba la URL a monitorear: ')
try:
    r = requests.head(url)
    if r.status_code == 200:
         print(url+' is UP')
    else:
         print(r.status_code)
except:
       print('Error en la URL')
import aiohttp
import asyncio

site = input("Introduzca el sitio: ")


async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get(site) as response:
            if response.status == 200:
                print(f"\n\nEl sitio: {site} Funciona perfectamente")
            elif response.status == 404:
                print(f"\n\nEl sitio: {site} no se encuentra")
            elif response.status == 403:
                print(f"\n\nEl sitio: {site} deniega el acceso")
            elif response.status == 500:
                print(f"\n\nEl sitio: {site} presenta Error de server Interno")         
            elif response.status == 502:
                print(f"\n\nEl sitio: {site} recibio una respuesra no valida del servidor ascendente")   
            elif response.status == 503:
                print(f"\n\nEl Sitio: {site} presenta Servicio No Disponible")
            else:
                print(f"\n\nEl Sitio: {site} esta caido")



    input("\n\nPresione cualquier tecla para salir del programa")



loop = asyncio.get_event_loop()
loop.run_until_complete(main())


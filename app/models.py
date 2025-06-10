from app.conexion import Conexion


def select_all():
    conectar = Conexion("select * from criptomonedas order by Fecha DESC")    
    filas = conectar.res.fetchall()
    columnas = conectar.res.description #columnas
    lista_diccionario=[]  

    for f in filas:
        diccionario={}    
        posicion=0
        for c in columnas:
            diccionario[c[0]] = f[posicion]
            posicion +=1
        lista_diccionario.append(diccionario)
    conectar.con.close()
    return lista_diccionario
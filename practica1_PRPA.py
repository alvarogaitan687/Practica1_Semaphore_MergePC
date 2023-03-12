"""

@author: Álvaro Gaitán Martín

"""
from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Value, Array
from time import sleep
import random

"""
Estructura de la práctica: 
La información esencial se registra en los siguientes objetos sincronizados 'estados_procesos' de tipo Array donde se tiene el estado del productor i-esimo
en la posicion i-esima {-2} si esta vacio, {-1} si ha finalizado {valor positivo} el valor producido, 'storage' de tipo Array donde iremos incorporando en orden
los elementos consumidos empleando un 'index' de tipo Value para conservar la posicion por donde vamos en el almacen, y dos listas de semaforos empty y non_empty 
que contienen los semaforos empty_i y non_empty_i de tipo Lock en la correspondiente posicion i-esima de los vectores. Ademas, empleamos un semaforo mutex te tipo Lock
para regular como sección crítica todos aquellos sitios donde modifiquemos estados_procesos. Observamos que no es necesario imponer como sección crítica la modificacion
de storage porque al haber solo un consumidor y por la estructura de los semaforos solo podra accederse por un proceso de forma contemporanea.

El codigo consta de los procesos de los productores y del consumidor: Inicialmente todos los estados_procesos de los productores están vacios {-2}, luego imponemos
mediante un for en consumidor que non_empty_i se bloquee para todos los productores, de forma que consumidor queda bloqueado hasta que todos los productores 
hayan producido un elemento. A continuación, el consumidor controla todos los semaforos de los productores de forma que una vez determinado cual es el proceso 
con el valor mas pequeño de todos los actuales, lo consume y libera el semaforo asociado al productor de la posicion que se acaba de consumir, quedando el consumidor
bloqueado hasta que dicho productor produzca un nuevo elemento o finalice. Simetricamente, todos los productores una vez realizada la primera produccion quedan bloqueados
a la espera de que el consumidor los libere cuando contengan el menor elemento de los vigentes en una determinada consumicion.

Para ello, empleamos dos funciones auxiliares, producir y consumir
Obs: Los productores generan elementos de forma creciente, para ello, cuando consumimos un elemento no los sustituimos por -2, lo dejamos para tener un registro 
del valor anterior y despues lo sobrescribimos en estados_procesos mediante un numero aleatorio superior.
Obs: En caso de tener K < N2*NPROD forzamos la parada de todos los productores imponiendo un -1 en su correspondiente casilla de estados_procesos esto repercute:
    -En producir: donde añadimos un condicional de forma que ignore si trata de producir una casilla con un -1
    -En productor: Imponiendo que deje el bucle en caso de haber terminado 
    -En consumidor: Imponiendo que deje el bucle en caso de haber terminado 
"""

def delay(factor = 3):
    sleep(random.random()/factor)

"""Observación: Si queremos consumir todos los elementos producidos, debemos tomar K > N2*NPROD
En caso de K < N2*NPROD forzamos la parada de todos los productores imponiendo un -1 en su correspondiente casilla de estados_procesos"""

N2= 2       #Numero de elementos producidos por productor
K = 70     #Numero maximo de elementos consumibles 
NPROD = 5  #Numero de productores

def producir(estados_procesos, i, mutex):
    mutex.acquire()
    try:
        if estados_procesos[i] != -1: #Para el caso K < N2*NPROD ignore si trata de producir una casilla con un -1 
            if estados_procesos[i]==-2: #Si esta vacio 
                valor_actual = 0
            else:
                valor_actual=estados_procesos[i] #Consideramos el valor recien consumido para producir otro mayor 
            estados_procesos[i] = random.randint(valor_actual,100000+valor_actual)
        delay(6)
    finally:
        mutex.release()
    
    
def consumir(storage, estados_procesos, index, i):
    storage[index.value] = estados_procesos[i]  #Añade el valor a consumir al almacen por la posicion actual 
    index.value += 1
    delay(6)
    
def productor (estados_procesos, i, empty, non_empty, mutex): 
    v = 0
    while (not terminado(estados_procesos)) and v < N2+1:
        delay(6)
        empty.acquire()
        producir(estados_procesos, i, mutex)
        #print('produzco', estados_procesos[i])
        non_empty.release()
        v+=1
    estados_procesos[i] = -1
    print ('he terminado')
    
"""        
def print_e(estados_procesos):
    for i in range(NPROD):
        print(estados_procesos[i])
"""
def print_s (storage):
    for i in range(len(storage)):
        if storage[i]!=0:
            print(storage[i])


def terminado (lista): #Funcion auxiliar: Determina si estados_procesos ha terminado (si todos sus elementos son -1)
    pos = 0
    while (pos < len(lista)) and (lista[pos] == -1):
        pos += 1
    return pos == len(lista)

def minimo_inicial(estados_procesos): #Funcion auxiliar: Toma como primer candidato a minimo el primer valor no negativo de estados_procesos 
    v=0
    while estados_procesos[v]<0:
        v+=1
    minimo=estados_procesos[v]
    return minimo
    
        
def consumidor(storage, estados_procesos, index, empty, non_empty, mutex):
    for i in non_empty: #Inicializacion: Exige a todos los procesos que produzcan un elemento 
        i.acquire()
    v=0
    while (not terminado(estados_procesos)) and v < K:
        minimo = minimo_inicial(estados_procesos)
        j = 0
        for i in range(NPROD): #Buscamos la posicion de estados_procesos que contenga el minimo positivo (debe ignorar los -1 asociados a los procesos finalizados)
            print(estados_procesos[i]) 
            if (estados_procesos[i]>0) and (estados_procesos[i]<=minimo):
                minimo=estados_procesos[i]
                j = i
        print('consumo', estados_procesos[j])
        if (not terminado(estados_procesos)): #Se repite la condicion para que en el caso de K < N2*NPROD si el proceso ha terminado asegurarnos no entre en esta seccion 
            consumir (storage, estados_procesos, index, j)
            empty[j].release()
            delay(6)
            non_empty[j].acquire()    
            v=v+1
    mutex.acquire() #En el caso K < N2*NPROD: El consumidor ha acabado paras todos los procesos imponiendo un -1 para todos los estados_procesos
    for i in range(NPROD):
        if (estados_procesos[i] != -1):
            estados_procesos[i] = -1
    mutex.release()
    for i in empty:
        i.release() #Liberas todos los semaforos para que hagan una iteracion en falso (producir no lo va a modificar), de esta forma para la siguiente iteracion el productor ha terminado 
    print_s(storage)
        

def main():
    estados_procesos = Array ('i', NPROD) #Valores de los productores {-1,-2,positivo}
    index=Value('i',0) #Posicion actual del almacen 
    for i in range (NPROD):
        estados_procesos[i] = -2
    storage = Array ('i', K) #Almacen: se van añadiendo en orden los elementos consumidos  
    empty = [] 
    non_empty = []
    mutex = Lock()
    for i in range(NPROD):
        empty.append(Lock())
        non_empty.append(Lock())
    for i in range (NPROD):
        non_empty[i].acquire()
    prodlst = [ Process(target=productor,
                        name=f'prod_{i}',
                        args=(estados_procesos, i, empty[i], non_empty[i], mutex))
                for i in range(NPROD) ]
    cons = [ Process(target=consumidor,
                      name="consumidor",
                      args=(storage, estados_procesos, index, empty, non_empty, mutex))]
    for p in prodlst + cons:
        p.start()

    for p in prodlst + cons:
        p.join()

if __name__ == '__main__':
    main()


    
    
    
    
    
    
    
    
    
    
    

"""
@author: Álvaro Gaitán Martín

"""

"""Estructura:
En esta parte mantiene la misma estructura conceptual que la practica principal que solo permite a cada productor 
producir de uno en uno. Con la diferencia de que ahora el productor puede producir todos sin necesidad de esperar al consumidor.
Para poder llevar esta distincion, en lugar de estados_procesos que conserva un solo valor para cada productor 
la informacion se llevara en una lista 'lista_arrays' que contendra un Array por cada productor con N2+1 espacios, y en lugar 
de emplear semaforos de tipo Lock, el consumidor llevara el control de cuando podra consumir (cuando no haya productores vacios)
empleando para cada productor dos semaforos uno empty de tipo BoundedSemaphore(N2) que le permitira producir hasta N2 elementos sin bloquearlo 
y un semaforo non_empty de tipo Semaphore(0) que bloqueara consumidor impidiendolo consumir solo si hay algun productor vacio. 

Obs: El valor actual de cada proceso correspondera con la posicion 0 de su array, y el resto de valores en espera se iran añadiendo en orden

Obs: Los productores generan numeros de forma creciente, para ello emplearemos una variable auxiliar sincronizada de tipo Value donde
registre el ultimo elemento consumido de forma que al producir un elemento, tiene que ser mayor que este o mayor que el elemento que le 
precede en caso de llevar varios elementos añadidos.

Obs: Definimos los arrays de los procesos de tamaño N2+1 para permitir tener un espacio donde colocar el -1 en caso de que el correspondiente
proceso haya terminado de producir todos sus elementos (N2) antes de que el consumidor consuma ninguno.

Obs: Al igual que en la otra practica distinguiremos el caso de K < N2*NPROD donde se impondra que todos los procesos tengan un -1
en su posicion actual (lista_arrays[i][0]) de forma que
    -En productor: Imponemos que deje el bucle en caso de haber terminado   (todos los procesos presentan un -1 en la posicion actual lista_arrays[i][0])
    -En consumidor: Imponemos que deje el bucle en caso de haber terminado  (todos los procesos presentan un -1 en la posicion actual lista_arrays[i][0])
"""
from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import Value, Array
from time import sleep
import random

def delay(factor = 3):
    sleep(random.random()/factor)

N2= 2       #Numero de elementos producidos por productor
K = 25     #Numero maximo de elementos consumibles 
NPROD = 5  #Numero de productores


def producir(lista_arrays, i, mutex, w, valor_act):
    try:
        mutex.acquire()
        if not terminado_proceso(lista_arrays[i]): #Para que no produzca en el caso de haber terminado el proceso(ya presente un -1 el correspondiente array)
            if w == 0: #Si es el primer numero que produce
                lista_arrays[i][0] = random.randint(1,1000)
            else:
                v = 0
                while (v<N2 and lista_arrays[i][v] != -2): #Buscamos el primer -2 del correspondiente array del proceso
                    v += 1
                if v == 0: #Si va a producir y hay un -2 es que se acaba de consumir su valor y por tanto el siguiente valor a producir basta que sea mayor que valor_act
                    lista_arrays[i][0] = random.randint(valor_act,1000+valor_act)
                else: #Si es una posicion de la 'recamara' para ser creciente basta que sea mayor que el anterior 
                    valor_actual=lista_arrays[i][v-1]
                    lista_arrays[i][v] = random.randint(valor_actual,1000+valor_actual)
        delay(6)
    finally:
        mutex.release()
        
def terminado_proceso (lista_arrays_i): #Funcion auxiliar: determina cuando ha terminado un proceso (si presenta algun -1 en el array correspondiente)
    contador = 0 
    for j in range(N2+1):
        if (lista_arrays_i[j] == -1):
            contador += 1
    return contador != 0
    
    
def consumir(storage, lista_arrays, index, i, mutex, valor_act):
    try:
        mutex.acquire()  
        storage[index.value] = lista_arrays[i][0]
        index.value += 1
        delay()
        valor_act.value = lista_arrays[i][0] #Conservamos el valor que se acaba de consumir para poder hacer creciente la seleccion de los siguientes valores en 'producir' 
        for j in range(N2): #Consumimos el valor que esta situado en la primera posicion del array del correspondiente proceso
            lista_arrays[i][j] = lista_arrays[i][j+1]
        if terminado_proceso(lista_arrays[i]): # Exigimos que el resto del array a partir del -1 valgan -2 (esten vacios)
            v = 0
            while (v<N2 and lista_arrays[i][v] != -1): #Buscamos el primer -1
                v += 1
            v += 1
            while (v<N2+1): 
                lista_arrays[i][v] = -2
                v += 1
    finally:
        mutex.release()
    
def productor (lista_arrays, i, empty, non_empty, mutex, valor_act): 
    v = 0
    while (not terminado(lista_arrays)) and v < N2: #`
        delay(6)
        empty[i].acquire()
        producir(lista_arrays, i, mutex, v, valor_act.value)
        non_empty[i].release()
        v+=1        
    mutex.acquire()
    v = 0
    while (v<N2 and lista_arrays[i][v] != -2):  #Buscamos la posicion que contiene el primer -2
        v += 1
    lista_arrays[i][v] = -1 #Situamos el -1 que determina su finalizacion
    mutex.release()
    print ('he terminado', v)
    non_empty[i].release()
    non_empty[i].release()
        
def print_e(lista_arrays): #Funcion auxiliar para la visualizacion
    for i in range(NPROD):
        for j in range (N2+1):
            if lista_arrays[i][j] != 0:
                print ('proceso', i, 'elem', lista_arrays[i][j])

def print_s (storage): #Funcion auxiliar para la visualizacion
    for i in range(len(storage)):
        if storage[i]!=0:
            print(storage[i])
            
def terminado (lista_arrays): #Funcion auxiliar que determina cuando todos los procesos han terminado (es decir, lista_arrays[i][0] = -1 para toda i)
    pos = 0
    while (pos < len(lista_arrays)) and (lista_arrays[pos][0] == -1):
        pos += 1
    return pos == len(lista_arrays)

def consumidor(storage, lista_arrays, index, empty, non_empty, mutex, valor_act):
    for i in non_empty: #Inicializacion: Exige a todos los procesos que produzcan un elemento 
        i.acquire()
        i.acquire()
    v=0
    while (not terminado(lista_arrays)) and v < K:
        minimo = 10000 
        j = 0
        print_e(lista_arrays)
        for i in range(NPROD): #Buscamos la posicion de lista_arrays[i][0] que contenga el minimo positivo (debe ignorar los -1 asociados a los procesos finalizados)
            if (lista_arrays[i][0]>0) and (lista_arrays[i][0]<minimo):
                minimo=lista_arrays[i][0]
                j = i
        print('consumo', lista_arrays[j][0], 'la j es', j)
        if (not terminado(lista_arrays)):  #Se repite la condicion para que en el caso de K < N2*NPROD si el proceso ha terminado asegurarnos no entre en esta seccion 
            consumir (storage, lista_arrays, index, j, mutex, valor_act)  
            empty[j].release()  
            print(non_empty[j])
            non_empty[j].acquire()
            v=v+1
            delay()
    mutex.acquire() 
    for i in range(NPROD):  #En el caso K < N2*NPROD: El consumidor ha acabado paras todos los procesos imponiendo un -1 para todo lista_arrays[i][0]
        if (lista_arrays[i][0] != -1):
            lista_arrays[i][0] = -1
    print_s(storage)
    mutex.release()

def main():
    lista_arrays = [] #Lista con los arrays de todos los proocesos 
    for i in range(NPROD):
        lista_arrays.append(Array ('i', N2+1))
    index=Value('i',0)  #Posicion actual del almacen
    valor_act=Value('i', 0) #Variable auxiliar que lleva el valor recien consumido
    for i in range (NPROD):
        for j in range (N2+1):
            lista_arrays[i][j] = -2
    storage = Array ('i', K) #Almacen 
    empty = []
    non_empty = []
    mutex = Lock()
    for i in range(NPROD):
        empty.append(BoundedSemaphore(N2)) 
        non_empty.append(Semaphore(0)) 
    prodlst = [ Process(target=productor,
                        name=f'prod_{i}',
                        args=(lista_arrays, i, empty, non_empty, mutex, valor_act))
                for i in range(NPROD) ]
    cons = [ Process(target=consumidor,
                      name="consumidor",
                      args=(storage, lista_arrays, index, empty, non_empty, mutex, valor_act))]
    for p in prodlst + cons:
        p.start()

    for p in prodlst + cons:
        p.join()

if __name__ == '__main__':
    main()
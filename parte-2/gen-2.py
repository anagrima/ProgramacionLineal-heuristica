#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, subprocess, tempfile
from pathlib import Path
import re

USAGE = "Uso: python gen-2.py <entrada.in> <salida.dat>"

# funcion para parsear una linea de numeros (separados por espacios o comas)
def parse_nums(linea):
    # admite espacios o comas como separadores
    partes = linea.replace(',', ' ').split() # reemplazar comas por espacios y dividir
    return [float(x) for x in partes] # convertir cada parte a float y devolver lista

# funcion principal
def main():
    # verificar argumentos
    if len(sys.argv) != 3: # si no hay 3 argumentos --> error
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    #rutas de fichero de entrada (.in) y salida (.dat)
    in_path = Path(sys.argv[1])
    dat_path = Path(sys.argv[2])

    # ruta del .mod
    mod_path = Path("parte-2-2.mod")

    # verificar existencia del .in
    if not in_path.exists(): # si no existe el fichero de entrada --> error
        print(f"Error: no existe el fichero de entrada: {in_path}", file=sys.stderr)
        sys.exit(2)
    # verificar existencia del modelo .mod
    if not mod_path.exists(): # si no existe el modelo .mod --> error
        print(f"Error: no se encontró el modelo: {mod_path.name}", file=sys.stderr)
        sys.exit(3)

    # leer .in
    lineas = []
    # abrimos fichero y leemos cada linea
    with in_path.open("r", encoding="utf-8") as fichero:
        for linea in fichero: # cada linea del fichero
            valor = linea.strip() # eliminar espacios en blanco al inicio y final
            #cada linea no vacia la guardamos
            if valor: # si la linea no esta vacia --> la guardamos
                lineas.append(valor)
    # verificar lineas esperadas
    try:
        # numero de franjas n, numero de autobuses m y numero de talleres u
        franja_bus_taller = parse_nums(lineas[0]) # primera linea
        if len(franja_bus_taller) != 3: # si no hay tres numeros en la primera linea --> error
            raise ValueError("Primera línea debe contener numero de franjas buses talleres")
        franjas = int(franja_bus_taller[0]) # numero de franjas
        buses = int(franja_bus_taller[1]) # numero de autobuses
        talleres = int(franja_bus_taller[2]) # numero de talleres

        # matriz de pasajeros comunes entre los autobuses ab (m filas, m columnas)
        suma_pasajeros = []
        index = 1
        for fila in range(buses): # cada fila de la matriz
            # analizamos linea a linea los datos proporcionados de la suma de pasajeros del autobus a con el autobus b 
            row = parse_nums(lineas[index]); index += 1
            # verificar longitud
            if len(row) != buses: # si la longitud de la fila no es igual al numero de buses --> error
                raise ValueError(f"Fila de pasajeros comunes con longitud {len(row)} != numero de buses ({buses})")
            suma_pasajeros.append(row)

            
        # matriz de disponibilidad de cada franja n para el taller u
        # (n filas, u columnas) — disponibilidad por (t,f)
        disponibilidad = []
        for fila in range(franjas): # cada fila de la matriz
            # analizamos linea a linea los datos proporcionados de la disponibilidad de cada franja para cada taller
            row = parse_nums(lineas[index]); index += 1
            # verificar longitud
            if len(row) != talleres: # si la longitud de la fila no es igual al numero de talleres --> error
                raise ValueError(f"Fila de disponibilidad con longitud {len(row)} != numero de talleres ({talleres})")
            # forzamos a 0/1 enteros por claridad
            disponibilidad.append([int(round(dispo)) for dispo in row])

    # capturar errores de parseo
    except Exception as e:
        print("Error al parsear el .in de 2.2.\n"
              "Formato esperado:\n"
              "<n> <m> <u>\n"
              "<c11 ... c1m>\n"
              "...\n"
              "<cm1 ... cmm>\n"
              "<o11 ... o1u>\n"
              "...\n"
              "<on1 ... onu>\n"
              f"Detalle: {e}", file=sys.stderr)
        sys.exit(4)

    # escribir el fichero de salida .dat
    with dat_path.open("w", encoding="utf-8") as salida:
        # conjuntos
        salida.write("set Autobuses := " + " ".join(str(bus) for bus in range(1, buses+1)) + ";\n") # todos los autobuses
        salida.write("set Franjas := " + " ".join(str(franja) for franja in range(1, franjas+1)) + ";\n") # todas las franjas
        salida.write("set Talleres := " + " ".join(str(taller) for taller in range(1, talleres+1)) + ";\n") # todos los talleres
        # parametro suma_pasajeros (m x m), indexado por bus_a, bus_b en Autobuses
        salida.write("param suma_pasajeros : " + " ".join(str(bus_b) for bus_b in range(1, buses+1)) + " :=\n")
        for bus_a in range(1, buses+1): # cada bus_a
            salida.write("  " + str(bus_a) + " " + " ".join(str(suma_pasajeros[bus_a-1][bus_b-1]) for bus_b in range(1, buses+1)) + "\n") # escribimos fila bus
        salida.write(";\n")
        salida.write("#matriz que representa la suma de pasajeros de los autobuses a y b\n")
        # parametro disponibilidad (n x u), escrito como filas franja (Franjas) y columnas taller (Talleres):
        salida.write("param disponibilidad : " + " ".join(str(taller) for taller in range(1, talleres+1)) + " :=\n")
        for franja in range(1, franjas+1): # cada franja
            salida.write("  " + str(franja) + " " + " ".join(str(disponibilidad[franja-1][taller-1]) for taller in range(1, talleres+1)) + "\n") # escribimos fila franja
        salida.write(";\n")
        salida.write("#matriz que representa la disponibilidad de franjas en cada taller, filas = franjas, columnas = talleres\n")
        salida.write("end;\n")
    
    # ejecutar GLPK y resolver
    with tempfile.TemporaryDirectory() as fichero_temporal: # crear un directorio temporal
        solucion_path = Path(fichero_temporal) / "solucion.sol" # ruta del fichero de solucion temporal
        
        # ejecutar glpsol
        try: 
            ejecucion = subprocess.run(
                ["glpsol", "--model", str(mod_path.resolve()), "--data", str(dat_path.resolve()), "--output", str(solucion_path.resolve())],
                capture_output=True, text=True, check=False
            )
        except FileNotFoundError: # si glpsol no se encuentra --> error
            print("Error: glpsol no está en PATH. Comprueba 'glpsol --version'.", file=sys.stderr)
            sys.exit(5)

        # verificar ejecucion correcta
        if ejecucion.returncode != 0 or not solucion_path.exists(): # si glpsol falla o no se genera el fichero de solucion --> error
            print("Error al ejecutar glpsol.", file=sys.stderr)
            sys.exit(6)
        
        # leer fichero de solucion
        sol_text = solucion_path.read_text(encoding="utf-8", errors="ignore")

        # extraer el estado de la solucion
        buscar_estado = re.search(r'^\s*Status:\s*(.+)$', sol_text, flags=re.M) # buscar linea de estado
        estado = buscar_estado.group(1).strip().upper() if buscar_estado else "" # extraer estado en mayusculas

        # comprobar el estado de la solucion
        if not estado: # si no se encuentra el estado --> error
            print("No se ha encontrado el valor óptimo", file=sys.stderr)
            sys.exit(7)

        # estados que NO permiten imprimir objetivo
        estado_malo = ("INFEASIBLE", "NO PRIMAL", "NO FEASIBLE", "UNDEFINED", "UNBOUNDED")
        if any(x in estado for x in estado_malo): # si el estado es malo --> error
            print("No se ha encontrado el valor óptimo", file=sys.stderr)
            sys.exit(7)

        # acepta solo soluciones óptimas (entera si hay binarias)
        estado_bueno = ("INTEGER OPTIMAL", "OPTIMAL")
        if not any(x in estado for x in estado_bueno): # si el estado no es bueno --> error
            print("No se ha encontrado el valor óptimo", file=sys.stderr)
            sys.exit(7)

        # ahora buscamos el objetivo
        buscar_objetivo = re.search(r'Objective:\s*[^\n=]*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', sol_text) # buscar el valor del objetivo
        if not buscar_objetivo: # si no se encuentra el objetivo --> error
            print("No se ha encontrado el valor óptimo", file=sys.stderr)
            sys.exit(7)
        valor_optimo = float(buscar_objetivo.group(1)) # convertir a float

        # buscar todas las asignaciones que valen 1 o 1.0
        patron = re.compile(
            r'(?m)^\s*(?:\d+\s+)?'
            r'Asignado\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]'
            r'\s*\*?\s*'
            r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b'
        )
        asignaciones = []
        for coincidencia in patron.finditer(sol_text): # cada coincidencia del patron
            bus, franja, taller = map(int, coincidencia.group(1, 2, 3)) # extraer indices
            actividad = float(coincidencia.group(4)) # extraer valor
            if abs(actividad - 1.0) < 1e-9: # si el valor es 1 --> asignacion
                asignaciones.append((bus, franja, taller))

        if not asignaciones: # si no hay asignaciones --> posible problema
            columnas = re.search(
                r'(?s)^Column name.*?$[-=]+\s*(.*?)(?:^\s*$|^Karush|^Row name)',
                sol_text, flags=re.M
            ) # extraer fragmento de columnas
            if columnas: # si se encontro el fragmento de columnas --> debug
                print("DEBUG: No hay Asignado=1. Fragmento de Columns:\n",
                      columnas.group(1)[:1000], file=sys.stderr)

    # conteo de variables y restricciones
    vars_asignaciones = buses * franjas * talleres
    vars_coincidencias = (buses * (buses - 1) // 2) * franjas
    #entre 2 para no tener en cuenta los duplicados
    num_vars = vars_asignaciones + vars_coincidencias

    # restricciones
    cons_asignado = buses         #cada bus necesita exactamente una asignacion, 1 restriccion asignado por cada bus
    cons_cap_max = franjas * talleres      #cada par (franja, taller) puede tener max 1 bus, cada combi franja taller hay una restricción    
    cons_dispo = buses * franjas * talleres    #si una franja no está disponible, no se puede asignar bus. restriccion para cada m, u, n. 
    cons_coinc = 3 * ((buses * (buses - 1) // 2) * franjas)
    #tenemos tres restricciones para cada par ab en cada franja
    num_cons = cons_asignado + cons_cap_max + cons_dispo + cons_coinc

    # verificar que se obtuvo el valor optimo
    if valor_optimo is None: # si no se obtuvo el valor optimo --> error
        print("No se ha encontrado el valor óptimo\n",file=sys.stderr)
        sys.exit(7)

    # imprimir resultados
    print(f"valor óptimo = {valor_optimo:.2f}, número de variables de decisión = {num_vars}, número de restricciones = {num_cons}")
    for a, f, t in sorted(asignaciones): # cada asignacion
        print(f"BUS {a} asignado a TALLER {t} en FRANJA {f}")

if __name__ == "__main__":
    main()

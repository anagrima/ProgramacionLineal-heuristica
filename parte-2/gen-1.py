#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, subprocess, tempfile, re
from pathlib import Path

USAGE = "Uso correcto: python gen-1.py <entrada.in> <salida.dat>"
# funcion para parsear una linea con numeros separados por espacios o comas
def parse_nums(linea):
    partes = linea.replace(',', ' ').split() # reemplazar comas por espacios y dividir
    return [float(x) for x in partes] # convertir a float

# funcion principal
def main(): 
    # verificar argumentos
    if len(sys.argv) != 3: # si no hay 3 argumentos --> error
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    #ruta de fichero de entrada (.in) y salida (.dat)
    in_path = Path(sys.argv[1])
    dat_path = Path(sys.argv[2])

    #ruta del .mod
    mod_path = Path("parte-2-1.mod")

    # verificar existencia del .in
    if not in_path.exists(): # si no existe el fichero de entrada --> error
        print(f"Error: no existe el fichero de entrada: {in_path}", file=sys.stderr)
        sys.exit(2)
    # verificar existencia del modelo
    if not mod_path.exists(): # si no existe el modelo --> error
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
        # numero de franjas n y numero de autobuses m
        franjas_buses = parse_nums(lineas[0]) # primera linea
        if len(franjas_buses) != 2: # si no hay dos numeros en la primera linea --> error
            raise ValueError("Primera línea debe contener n m")
        franjas = int(franjas_buses[0]) # numero de franjas
        buses = int(franjas_buses[1]) # numero de autobuses

        #coste_distancia, kd y coste_pasajeros, kp
        coste_dis_pas = parse_nums(lineas[1])
        if len(coste_dis_pas) != 2: # si no hay dos numeros en la segunda linea --> error
            raise ValueError("Segunda línea debe contener kd kp")
        coste_distancia = coste_dis_pas[0] # coste por distancia
        coste_pasajeros = coste_dis_pas[1] # coste por pasajero
        
        #para los dos valores siguientes nos aseguramos de que 
        #el tamaño de la lista coicnide con el numero de buses que tenemos
        #cada bus m debe tener una distancia y un número de pasajeros

        #distancia a la que se encuentra el bus n del taller
        dis_vals = parse_nums(lineas[2]); assert len(dis_vals) == buses
        #numero de pasajeros del autobus n
        pas_vals = parse_nums(lineas[3]); assert len(pas_vals) == buses
    # capturar errores de parseo
    except Exception as e:
        print("Error al parsear el .in. Formato esperado:\n"
              "<n> <m>\n<kd> <kp>\n<d1 ... dm>\n<p1 ... pm>", file=sys.stderr)
        sys.exit(4)

    # escribimos el fichero de salida .dat
    with dat_path.open("w", encoding="utf-8") as salida:
        # conjuntos
        salida.write("set Autobuses := " + " ".join(str(bus) for bus in range(1, buses+1)) + ";\n") #todos los autobuses
        salida.write("set Franjas := " + " ".join(str(franja) for franja in range(1, franjas+1)) + ";\n") #todas las franjas
        # parametros
        salida.write(f"param coste_distancia := {coste_distancia};\n") # coste por distancia
        salida.write(f"param coste_pasajeros := {coste_pasajeros};\n") # coste por pasajero
        salida.write("param distancia :=\n")
        #distancia de cada autobus d[a]
        for bus in range(1, buses+1): # cada autobus
            salida.write(f"  {bus} {dis_vals[bus-1]}\n") # escribir distancia
        salida.write(";\n") 
        salida.write("param pasajero :=\n")
        # escribir el numero de pasajeros de cada autobus p[a]
        for bus in range(1, buses+1): # cada autobus
            salida.write(f"  {bus} {pas_vals[bus-1]}\n") # escribir numero de pasajeros
        salida.write(";\n")
        salida.write("end;\n")

    # ejecutar GLPK y recoger informacion
    with tempfile.TemporaryDirectory() as fichero_temporal: # crear un directorio temporal
        solucion_path = Path(fichero_temporal) / "solucion.sol" # ruta del fichero de solucion temporal

        # ejecutar glpsol
        try:
            ejecucion = subprocess.run(
                ["glpsol",
                 "--model", str(mod_path.resolve()),
                 "--data",  str(dat_path.resolve()),
                 "--output", str(solucion_path.resolve())],
                capture_output=True, text=True, check=False
            )
        except FileNotFoundError: # si no se encuentra glpsol --> error
            print("Error: glpsol no está en PATH. Ejecuta 'glpsol --version' para comprobar.", file=sys.stderr)
            sys.exit(5)

        # verificar ejecucion correcta
        if ejecucion.returncode != 0 or not solucion_path.exists(): # si glpsol falla o no se genera el fichero de solucion --> error
            print("Error al ejecutar glpsol.", file=sys.stderr)
            sys.exit(6)

        # leer fichero de solucion
        sol_text = solucion_path.read_text(encoding="utf-8", errors="ignore")

        # parseo robusto del informe
        # objetivo
        buscar_objetivo = re.search(r'Objective:\s*[^\n=]*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', sol_text) # buscar el valor del objetivo
        valor_optimo = float(buscar_objetivo.group(1)) if buscar_objetivo else None # convertir a float si se encuentra

        # asignados y sin asignar
        asignados = []     # (a,f)
        sin_asignados = []  # a

        lineas = sol_text.splitlines() # dividir el texto en lineas

        # nombre en primera linea
        buscar_asign = re.compile(r'^\s*\d+\s+asignado\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*$', re.I) # buscar asignados
        buscar_sinasign = re.compile(r'^\s*\d+\s+sin_asignar\[\s*(\d+)\s*\]\s*$', re.I) # buscar sin asignar
        # en la segunda linea, tomamos el PRIMER num como Activity (mejor que “el ultimo”)
        primer_numero = re.compile(r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')

        # recorrer lineas
        index = 0
        while index < len(lineas):
            linea = lineas[index]

            # buscar asignado
            valor_asign = buscar_asign.match(linea)
            if valor_asign: # si se encuentra asignado --> leer bus y franja
                bus = int(valor_asign.group(1)); franja = int(valor_asign.group(2))
                # leer la siguiente línea con los numeros
                if index + 1 < len(lineas): # si hay una siguiente linea --> buscar actividad
                    siguiente_linea = lineas[index + 1]
                    buscar_actividad = primer_numero.search(siguiente_linea)
                    if buscar_actividad: # si se encuentra actividad --> convertir a float
                        actividad = float(buscar_actividad.group(1))
                        if abs(actividad - 1.0) < 1e-9: # si la actividad es 1.0 --> asignado
                            asignados.append((bus, franja))
                index += 2
                continue

            # buscar sin_asignar
            valor_sinasign = buscar_sinasign.match(linea)
            if valor_sinasign: # si se encuentra sin_asignar --> leer bus
                bus = int(valor_sinasign.group(1))
                if index + 1 < len(lineas): # si hay una siguiente linea --> buscar actividad
                    siguiente_linea = lineas[index + 1]
                    buscar_actividad = primer_numero.search(siguiente_linea)
                    if buscar_actividad: # si se encuentra actividad --> convertir a float
                        actividad = float(buscar_actividad.group(1))
                        if abs(actividad - 1.0) < 1e-9: # si la actividad es 1.0 --> sin asignar
                            sin_asignados.append(bus)
                index += 2
                continue

            # tambien por si GLPK alguna vez lo imprime todo en una sola linea
            una_linea_asignar = re.match(
                r'^\s*\d+\s+asignado\[\s*(\d+)\s*,\s*(\d+)\s*\]\s+\*?\s*' +
                r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', linea, re.I) # buscar asignado en una sola linea
            if una_linea_asignar: # si se encuentra asignado en una sola linea
                bus = int(una_linea_asignar.group(1)); franja = int(una_linea_asignar.group(2)) # leer bus y franja
                actividad = float(una_linea_asignar.group(3)) # leer actividad
                if abs(actividad - 1.0) < 1e-9: # si la actividad es 1.0 --> asignado
                    asignados.append((bus, franja))
                index += 1
                continue

            una_linea_sinasignar = re.match(
                r'^\s*\d+\s+sin_asignar\[\s*(\d+)\s*\]\s+\*?\s*' +
                r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', linea, re.I) # buscar sin_asignar en una sola linea
            if una_linea_sinasignar: # si se encuentra sin_asignar en una sola linea
                bus = int(una_linea_sinasignar.group(1)) # leer bus
                actividad = float(una_linea_sinasignar.group(2)) # leer actividad
                if abs(actividad - 1.0) < 1e-9: # si la actividad es 1.0 --> sin asignar
                    sin_asignados.append(bus)
                index += 1
                continue

            index += 1

    # salida con el MISMO formato que el .mod
    if valor_optimo is None: # si no se obtuvo el valor optimo --> error
        print("No se ha encontrado el valor óptimo", file=sys.stderr)
        sys.exit(7)

    # contar variables y restricciones
    num_variables = buses * franjas + buses 
    num_constantes = buses + franjas

    # verificar que se obtuvo el valor optimo
    if valor_optimo is None: # si no se obtuvo el valor optimo --> error
        print("No se pudo recuperar el valor óptimo desde la salida de GLPK.", file=sys.stderr)
        sys.exit(7)
    # imprimir resultados, valor óptimo encontrado, numero de variables y numero de restrricciones
    print(f"valor óptimo = {valor_optimo:.2f}, número de variables de decisión = {num_variables}, número de restricciones = {num_constantes}")
    for bus, franja in sorted(asignados): # si hay buses asignados
        print(f"BUS {bus} asignado a FRANJA {franja}")
    for bus in sorted(sin_asignados): # si hay buses sin asignar
        print(f"BUS {bus} -> NO ASIGNADO")

if __name__ == "__main__":
    main()

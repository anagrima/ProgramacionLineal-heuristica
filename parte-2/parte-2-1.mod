# parte-2-1.mod — Parte 2.2.1 (un taller, n franjas, m autobuses)

# definimos los conjuntos de autobuses y franjas horarias del taller
set Autobuses;     
set Franjas;           

# parametros
param coste_distancia >= 0;            # €/km si el bus se atiende (kd)
param coste_pasajeros >= 0;            # €/pasajero si NO se atiende (kp)
param distancia{a in Autobuses} >= 0;     # distancia del bus a al taller
param pasajero{a in Autobuses} >= 0;     # pasajeros del bus a

# variables de decision, binarias
var asignado{a in Autobuses, f in Franjas} binary;   # 1 si el bus a se asigna a la franja f
var sin_asignar{a in Autobuses}          binary;  # 1 si el bus a queda sin asignar

# función objetivo: minimizacion del imacto de averias
# coste total -> atender a en f cuesta coste_distancia * distanca[a]; 
# no atender a cuesta: coste_pasajeros * pasajeros[a]
minimize CosteTotal:
    sum {a in Autobuses, f in Franjas} coste_distancia * distancia[a] * asignado[a,f]
  + sum {a in Autobuses}        coste_pasajeros * pasajero[a] * sin_asignar[a];

# restricciones
# 1 - cada bus: o se asigna exactamente a una franja o queda sin asignar
s.t. cap_max_asignacion {a in Autobuses}:
    sum {f in Franjas} asignado[a,f] + sin_asignar[a] = 1;

# 2 - capacidad del taller: como mucho 1 bus por franja
s.t. cap_taller {f in Franjas}:
    sum {a in Autobuses} asignado[a,f] <= 1;

end;

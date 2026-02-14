# parte-2-2.mod — Parte 2.2

# definimos los conjuntos de autobuses, franjas horarias y talleres
set Autobuses;               
set Franjas;                
set Talleres;                 

# parametros
param suma_pasajeros{a in Autobuses, b in Autobuses} >= 0;            # suma de pasajeros entre buses a y b (matriz m x m) en caso de que estos coincidan
param disponibilidad{f in Franjas, t in Talleres} integer, >= 0, <= 1;   # disponibilidad de la franja f en el taller t; 0 ocupada, 1 libre

# variables de decision
var Asignado{a in Autobuses, f in Franjas, t in Talleres} binary;             # 1 si bus a es asignado a (f,t)
var Coinciden{a in Autobuses, b in Autobuses, f in Franjas: a < b} binary;    # 1 si a y b coinciden en franja f (en talleres distintos)
#usamos a < b para evitar duplicados (ab, ba coinciden, solo tenemos en cuenta ab)

# funcion objetivo: minimizar el solapamiento de pasajeros comunes entre ab en una misma franja
minimize UsuariosCoinc:
    sum {a in Autobuses, b in Autobuses: a < b} sum {f in Franjas} suma_pasajeros[a,b] * Coinciden[a,b,f];

# restricciones
# 1 - asignacion unica por autobus: cada autobus asignado a una sola combinacion de franja y taller
s.t. AsignacionUnica {a in Autobuses}:
    sum {f in Franjas, t in Talleres} Asignado[a,f,t] = 1;

# 2 - capacidad maxima por (f,t), maximo un autobus por franja en cada taller
s.t. CapMaxima {f in Franjas, t in Talleres}:
    sum {a in Autobuses} Asignado[a,f,t] <= 1;

# 3 - disponibilidad: la franja puede no estar disponible (0)
s.t. Disponibilidad {a in Autobuses, f in Franjas, t in Talleres}:
    Asignado[a,f,t] <= disponibilidad[f,t];

# 4 - enlace de coincidencias (linearizacion)

#acotamos Coinciden por arriba en caso de que a o b no estén asignados
#si a o b no está asignado entonces Coinciden no puede ser 1

s.t. CoincidenciaA {a in Autobuses, b in Autobuses, f in Franjas: a < b}:
    Coinciden[a,b,f] <= sum {t in Talleres} Asignado[a,f,t];

s.t. CoincidenciaB {a in Autobuses, b in Autobuses, f in Franjas: a < b}:
    Coinciden[a,b,f] <= sum {t in Talleres} Asignado[b,f,t];

#si a está asignado y b está asignado, var Coinciden si o si debe ser 1
s.t. CoincidenciaAB {a in Autobuses, b in Autobuses, f in Franjas: a < b}:
    Coinciden[a,b,f] >= sum {t in Talleres} Asignado[a,f,t] + sum {t in Talleres} Asignado[b,f,t] - 1;

end;

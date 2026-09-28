"""
Actividad 
Ahora invierte la lista de nums para poder ver los elementos de la lista [diez, rojo]
Al final crea una nueva lista ambos elementos e imprimir la nueva lista
"""
nums=['uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez']
colors=['rojo', 'azul', 'verde', 'amarillo', 'naranja', 'morado', 'rosa', 'gris', 'negro', 'blanco']
new_list = []

nums.reverse()


for num in nums:
    output = f"[{num}, {colors[nums.index(num)]}]"

    new_list.append(output)
    

print(new_list)



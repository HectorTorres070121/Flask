week = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
out = []
for i, day in enumerate(week):
    if (day == 'sabado' or day == 'domingo'):
        out.append(i)
print(out)

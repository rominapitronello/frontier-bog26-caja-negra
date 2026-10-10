# búsqueda fuera de línea (sin consultar el original) de una fórmula simple para el dígito de control,
# sobre los 20 ejemplos. 10 oct 10:1x bog: ninguna calza. uso: python3 herramientas/control_formulas.py material/pruebas/ejemplos.jsonl
import json, zlib, itertools, sys
ej=[json.loads(l) for l in open(sys.argv[1])]
# casos con control válido: los que no dan E201/E202
pares=[]
for r in ej:
    m=r["request"]["m"]; cuerpo,_,c=m.rpartition(";")
    if r["response"].get("error") in ("E201","E202","E301","E302"): continue
    if not c.isdigit(): continue
    pares.append((cuerpo,int(c)))
malo=[(r["request"]["m"].rpartition(";")[0],int(r["request"]["m"].rpartition(";")[2])) for r in ej if r["response"].get("error")=="E202"]
print(len(pares),"válidos;",malo,"inválido")
def prueba(nombre,f):
    if all(f(b)==c for b,c in pares) and all(f(b)!=c for b,c in malo): print("CALZA:",nombre)
transf={"tal cual":lambda s:s,"upper":str.upper,"lower":str.lower}
for tn,t in transf.items():
  for sep in (True,False):
    def base(s,t=t,sep=sep): s=t(s); return s if sep else s.replace(";","")
    for m in range(2,1000):
        prueba(f"{tn} sep={sep} sum(ord)%{m}", lambda s,m=m,base=base: sum(map(ord,base(s)))%m)
        prueba(f"{tn} sep={sep} sum(i*ord)%{m}", lambda s,m=m,base=base: sum((i+1)*ord(ch) for i,ch in enumerate(base(s)))%m)
        prueba(f"{tn} sep={sep} crc32%{m}", lambda s,m=m,base=base: zlib.crc32(base(s).encode())%m)
        prueba(f"{tn} sep={sep} adler%{m}", lambda s,m=m,base=base: zlib.adler32(base(s).encode())%m)
        prueba(f"{tn} sep={sep} sum(utf8)%{m}", lambda s,m=m,base=base: sum(base(s).encode())%m)

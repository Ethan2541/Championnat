# 28627904 LUONG Ethan
# 21304385 PHAM Louis-Antoine

from itertools import combinations
import math
import os
import signal

""" Modélisation """

# Il y a mjxy = nj*ne*ne sans la contrainte x != y

def codage(ne, nj, j, x, y):
    assert(ne > 0)
    assert(j <= nj-1 and j >= 0)
    assert(x <= ne-1 and x >= 0)
    assert(x <= ne-1 and x >= 0)
    return j*ne**2 + x*ne + y + 1

# On peut voir k comme un mot en base ne avec 3 chiffres : j, x, y
def decodage(k, ne):
    assert(ne > 0)
    y = (k-1) % ne
    x = ((k-1) // ne) % ne
    j = (k-1) // ne**2
    return j, x, y


""" Génération d'un planning de matchs """

def au_moins(L):
    assert(not any([v <= 0 for v in L]))
    if len(L) == 0:
        return ''
    return ' '.join([str(v) for v in L]) + ' 0\n'

# Encodage par paires
def au_plus(L):
    assert(not any([v <= 0 for v in L]))
    contrainte = ''
    for i in range(len(L)):
        for j in range(i+1, len(L)):
            contrainte += f'{-L[i]} {-L[j]} 0\n'
    return contrainte

def encoderC1(ne, nj):
    assert(ne > 0 and nj > 0)
    C1 = ''
    for j in range(nj):
        for x in range(ne):
            mjxy = [codage(ne, nj, j, x, y) for y in range(ne) if y != x] + [codage(ne, nj, j, y, x) for y in range(ne) if y != x]
            C1 += au_plus(mjxy)
    return C1, len(C1.split('\n'))-1

def encoderC2(ne, nj):
    assert(ne > 0 and nj > 0)
    C2 = ''
    for x in range(ne):
        for y in range(x+1, ne):
            mjxy = [codage(ne, nj, j, x, y) for j in range(nj)]
            mjyx = [codage(ne, nj, j, y, x) for j in range(nj)]
            C2 += au_moins(mjxy) + au_plus(mjxy)
            C2 += au_moins(mjyx) + au_plus(mjyx)
    return C2, len(C2.split('\n'))-1

def encoderC0(ne, nj):
    assert(ne > 0 and nj > 0)
    L = [codage(ne, nj, j, x, x) for x in range(ne) for j in range(nj)]
    C0 = ' 0\n'.join([str(-v) for v in L]) + ' 0\n'
    return C0, len(C0.split('\n'))-1

def encoder(ne, nj):
    assert(ne > 0 and nj > 0)
    C0, n0 = encoderC0(ne, nj)
    C1, n1 = encoderC1(ne, nj)
    C2, n2 = encoderC2(ne, nj)
    return f'p cnf {nj*ne**2} {n0+n1+n2}\n{C0}{C1}{C2}'

def dico_equipes(filename='equipes.txt'):
    dico = {}
    with open(filename, 'r') as f:
        lignes = f.readlines()
        for i, ligne in enumerate(lignes):
            dico[i] = ligne
        return dico

def decoder(ne, equipes):
    equipes = dico_equipes(equipes)
    solution = ''
    with open('resultats.txt', 'r') as f:
        lignes = f.readlines()
        for ligne in lignes:
            tokens = ligne.split()
            if len(tokens) == 0:
                continue
            if tokens[0] == 's' and tokens[1] == 'UNSATISFIABLE':
                return 'UNSAT'
            elif tokens[0] == 'v':
                for v in tokens[1:]:
                    if int(v) > 0:
                        j, x, y = decodage(int(v), ne)
                        solution += f'Jour {j} : {equipes[x][:-1]} (dom.) vs {equipes[y][:-1]} (ext.)\n'
    return solution
            
def programme(ne, nj, equipes):
    os.system(f'echo "{encoder(ne, nj)}" | ../glucose/simp/glucose -model > resultats.txt')
    return decoder(ne, equipes)


""" Optimisation du nombre de jours """

class TimeoutError(Exception):
    pass

def signal_handler(signum, frame):
    raise TimeoutError

def optimiser_nj_selon_ne(equipes, ne_min=3, ne_max=10, timeout=10):
    for ne in range(ne_min, ne_max+1):
        nj_min = 2*(ne-1)
        nj_max = ne*(ne-1)
        nj_inf = nj_min
        while nj_min <= nj_max:
            nj = (nj_max + nj_min) // 2
            signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(timeout)
            try:
                solution = programme(ne, nj, equipes)
            except TimeoutError:
                solution = 'Timeout'
            finally:
                signal.alarm(0)
                if solution != 'UNSAT':
                    has_timeout = solution == 'Timeout'
                    nj_max = nj - 1
                    nj_inf = nj
                else:
                    nj_min = nj + 1
        print(f'Pour ne = {ne}, on a nj_inf = {nj_inf} ({has_timeout and "Timeout" or "OK"})')


""" Equilibrer les déplacements et les week-ends """

def au_plus_etendu(L, k):
    contrainte = ''
    combinaisons = list(combinations(L, k+1))
    for sous_liste in combinaisons:
        contrainte += ' '.join([str(-v) for v in sous_liste]) + ' 0\n'
    return contrainte

def au_moins_etendu(L, k):
    N = len(L)
    return au_plus_etendu([-v for v in L], N-k)

def encoderC3(ne, nj, p_ext=0.5, p_dom=0.4):
    assert(ne > 0 and nj > 0)
    assert(p_ext >= 0 and p_ext <= 1)
    assert(p_dom >= 0 and p_dom <= 1)
    C3 = ''
    for x in range(ne):
        L_ext = [codage(ne, nj, dimanche, y, x) for y in range(ne) if y != x for dimanche in range(1, nj, 2)]
        C3 += au_moins_etendu(L_ext, math.ceil(p_ext*(ne-1)))
        L_dom = [codage(ne, nj, dimanche, x, y) for y in range(ne) if y != x for dimanche in range(1, nj, 2)]
        C3 += au_moins_etendu(L_dom, math.ceil(p_dom*(ne-1)))
    return C3, len(C3.split('\n'))-1

def encoderC4(ne, nj):
    assert(ne > 0 and nj > 0)
    C4 = ''
    for x in range(ne):
        for j in range(nj-2):
            L_ext = [codage(ne, nj, j, y, x) for y in range(ne) if y != x] + [codage(ne, nj, j+1, y, x) for y in range(ne) if y != x] + [codage(ne, nj, j+2, y, x) for y in range(ne) if y != x]
            C4 += au_plus_etendu(L_ext, 2)
            L_dom = [codage(ne, nj, j, x, y) for y in range(ne) if y != x] + [codage(ne, nj, j+1, x, y) for y in range(ne) if y != x] + [codage(ne, nj, j+2, x, y) for y in range(ne) if y != x]
            C4 += au_plus_etendu(L_dom, 2)
    return C4, len(C4.split('\n'))-1

def encoder_etendu(ne, nj):
    assert(ne > 0 and nj > 0)
    C0, n0 = encoderC0(ne, nj)
    C1, n1 = encoderC1(ne, nj)
    C2, n2 = encoderC2(ne, nj)
    C3, n3 = encoderC3(ne, nj)
    C4, n4 = encoderC4(ne, nj)
    return f'p cnf {nj*ne**2} {n0+n1+n2+n3+n4}\n{C0}{C1}{C2}{C3}{C4}'

def programme_etendu(ne, nj, equipes):
    os.system(f'echo "{encoder_etendu(ne, nj)}" | ../glucose/simp/glucose -model > resultats.txt')
    return decoder(ne, equipes)


""" Exécution """

if __name__ == '__main__':
    print(programme(3, 4, 'equipes.txt'))
    optimiser_nj_selon_ne('equipes.txt')
    print(programme_etendu(3, 9, 'equipes.txt'))
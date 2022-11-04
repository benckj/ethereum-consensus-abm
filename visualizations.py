import networkx as nx
import numpy as np
import matplotlib as plt
from matplotlib.patches import Rectangle


def blockchain_layout(G, relative = False):
    F = G.reverse()
    position = layout_algorithm(F)
    position = inverse_position_dict(position)
    
    if relative:
        max_x= max([v[0] for v in position.values()])
        max_y= max([v[1] for v in position.values()])
        if max_y==0:
            max_y=1

        for k,v in position.items():
            position[k]=(v[0]/max_x,v[1]/max_y)

    return position

def blockchain_layout_slot(G, relative = False):
    F = G.reverse()
    
    position = slot_algorithm(F)
    position = inverse_position_dict(position)
    
    if relative:
        max_x= max([v[0] for v in position.values()])
        max_y= max([v[1] for v in position.values()])
        if max_y==0:
            max_y=1

        for k,v in position.items():
            position[k]=(v[0]/max_x,v[1]/max_y)

    return position
    
def inverse_position_dict(pos):
    inv = {}
    for x, ys in pos.items():
        for y, block in ys.items():
            inv[block] = np.array([x,y])
    return inv

def layout_algorithm(G, pos = {}, K=None, inv={}):
    if not K:   
        K=G.copy()
    if len(G)==0:
        return pos

    all_paths=[]
    if len(G.edges()) != 0:
        #could only check the leaves
        for n in G.nodes():
            for m in G.nodes():
                if n == m:
                    continue
                else:
                    for path in nx.all_simple_paths(G,n,m):
                        all_paths.append(path)

        all_paths.sort(key=len,reverse=True)

        x=0
        y=0
        for i,n in enumerate(all_paths[0]):
            if i==0 and K.in_degree(n) != 0:
                for p in K.predecessors(n):
                    if p in inv.keys():
                        x+=inv[p][0]+1   
                y = max([max(list(pos[x+j].keys())) for j in range(len(all_paths[0]))])+1 
                pos[x][y]=n 

            elif x in pos.keys():
                pos[x][y]=n

            else:
                pos[x]={0:n}

            x+=1

    else:
        for n in G.nodes():
            for p in K.predecessors(n):
                x = inv[p][0]+1
                y = max(pos[x].keys())+1
                pos[x][y] = n

    inv = inverse_position_dict(pos)   
    H = G.copy()
    H.remove_nodes_from(list(inv.keys()))
    pos = layout_algorithm(H, pos=pos,K=K,inv=inv)
    
    return pos

def slot_algorithm(G, pos = {}, K=None, inv={}):
    if not K:   
        K=G.copy()
    if len(G)==0:
        return pos

    all_paths=[]

    if len(G.edges()) != 0:
        #could only check the leaves
        for n in G.nodes():
            for m in G.nodes():
                if n == m:
                    continue
                else:
                    for path in nx.all_simple_paths(G,n,m):
                        all_paths.append(path)

        all_paths.sort(key=len,reverse=True)
        y=0
        for i,n in enumerate(all_paths[0]):
            x=n.id
            if i==0 and K.in_degree(n) != 0:
                for j in all_paths[0]:
                    if j.id in pos.keys():
                        max_y = max(list(pos[j.id].keys()))
                        if max_y > y:
                            y = max_y
                pos[x]={y:n} 
            else:
                pos[x]={y:n}

            x+=1

    else:
        for n in G.nodes():
            for p in K.predecessors(n):
                x = n.id
                y = -1
                pos[x]={y:n}

    inv = inverse_position_dict(pos)   
    H = G.copy()
    H.remove_nodes_from(list(inv.keys()))
    pos = slot_algorithm(H, pos=pos,K=K,inv=inv)
    
    return pos

# def draw_chain(node):
#     print('new_block pre')
    

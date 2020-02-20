"""
Homology and Smith Normal Form
==============================
The purpose of computing the Homology groups for data generated 
hypergraphs is to identify data sources that correspond to interesting 
features in the topology of the hypergraph. 

The elements of one of these Homology groups are generated by $k$ 
dimensional cycles of relationships in the original data that are not 
bound together by higher order relationships. Ideally, we want the 
briefest description of these cycles; we want a minimal set of 
relationships exhibiting interesting cyclic behavior. This minimal set 
will be a bases for the Homology group.

The cyclic relationships in the data are discovered using a **boundary 
map** represented as a matrix. To discover the bases we compute the 
**Smith Normal Form** of the boundary map.

Homology Mod2
-------------
This module computes the homology groups for data represented as an
abstract simplicial complex with chain groups $\{C_k\}$ and $Z_2$ additions.  
The boundary matrices are represented as rectangular matrices over $Z_2$.
These matrices are diagonalized and represented in Smith
Normal Form. The kernel and image bases are computed and the Betti
numbers and homology bases are returned.

Methods for obtaining SNF for Z/2Z are based on Ferrario's work:
http://www.dlfer.xyz/post/2016-10-27-smith-normal-form/
"""

import numpy as np
import hypernetx as hnx
import warnings, copy
from hypernetx import HyperNetXError

def kchainbasis(h,k):
    """
    Compute the set of k dimensional cells in the abstract simplicial 
    complex associated with the hypergraph. 

    Parameters
    ----------
    h : hnx.Hypergraph
    k : int
        dimension of cell
    
    Returns
    -------
     : list
        an ordered list of kchains represented as tuples of length k+1

    See also
    --------
    hnx.hypergraph.toplexes

    Notes
    -----
    - Method works best if h is simple [Berge], i.e. no edge contains another and there are no duplicate edges (toplexes). 
    - Hypergraph node uids must be sortable.

    """

    import itertools as it
    kchains = set()
    for e in h.edges():
        if len(e) == k+1:
            kchains.add(tuple(sorted(e.uidset)))
        elif len(e) > k+1:
            kchains.update(set(it.combinations(sorted(e.uidset),k+1)))
    return sorted(list(kchains))

def interpret(Ck,arr):

    """
    Returns the data as represented in Ck associated with the arr
    
    Parameters
    ----------
    Ck : list
        a list of k-cells being referenced by arr
    arr : np.array
        a 0-1 array
    
    Returns
    ----
    : list
        list of k-cells referenced by data in Ck
    
    """

    output = list()
    for vec in arr:
        if len(Ck) != len(vec):
            raise HyperNetXError('elements of arr must have the same length as Ck')
        output.append([Ck[idx] for idx in range(len(vec)) if vec[idx] == 1])
    return output

def bkMatrix(km1basis,kbasis):
    """
    Compute the boundary map from $C_{k-1}$-basis to $C_k$ basis with 
    respect to $Z_2$
    
    Parameters
    ----------
    km1basis : indexable iterable 
        Ordered list of $k-1$ dimensional cell 
    kbasis : indexable iterable 
        Ordered list of $k$ dimensional cells
    
    Returns
    -------
    bk : np.array
        boundary matrix in $Z_2$
    """

    bk = np.zeros((len(km1basis),len(kbasis)),dtype=int)
    for cell in kbasis:
        for idx in range(len(cell)):
            face = cell[:idx]+cell[idx+1:]
            row = km1basis.index(face)
            col = kbasis.index(cell)
            bk[row,col]= 1
    return bk

def _rswap(i,j,M): 
    """
    Swaps ith and jth row of M
    Returns a new matrix 
    
    Parameters
    ----------
    i : int
    j : int
    M : np.array
    
    Returns
    -------
    N : np.array
        copy of M with ith and jth row exchanged
    """
    N = copy.deepcopy(M)
    N[i] = M[j]
    N[j] = M[i]
    return N

def _cswap(i,j,M):
    """
    Swaps ith and jth column of M
    Returns a new matrix 

    Parameters
    ----------
    i : int
    j : int
    M : np.array
    
    Returns
    -------
    N : np.array
        copy of M with ith and jth column exchanged    
    """    
    N = _rswap(i,j,M.transpose())
    return N.transpose()

def swap_rows(i,j,*args):
    """
    Swaps ith and jth row of each matrix in args
    Returns a list of new matrices 
    
    Parameters
    ----------
    i : int
    j : int
    M : np.array
    args : np.arrays
    
    Returns
    -------
    list
        list of np.arrays, copies of args with ith and jth row swapped
    """
    output = list()
    for M in args:
        output.append(_rswap(i,j,M))
    return output

def swap_columns(i,j,*args):
    """
    Swaps ith and jth column of each matrix in args
    Returns a list of new matrices

    Parameters
    ----------
    i : int
    j : int
    M : np.array
    args : np.arrays
    
    Returns
    -------
    list
        list of np.arrays, copies of args with ith and jth column 
        swapped
    """
    output = list()
    for M in args:
        output.append(_cswap(i,j,M))
    return output

def add_to_row(M,i,j,ri=1,rj=1,mod=2):
    """
    Replaces row i (of M) with sum ri multiple of ith row and rj multiple of jth row
    
    Parameters
    ----------
    M : np.array
        matrix
    i : int
        index of row being altered
    j : int
        index of row being added to altered
    ri : int, optional
        Multiplier for ith row
    rj : int, optional
        Multiplier for jth row
    mod : int, optional 
        modular addition to be used
    
    Returns
    -------
    N : np.array
        copy of M with ith row replaced with sum of multiples of ith row
        and jth row
    """
    N = copy.deepcopy(M)
    N[i] = np.mod(ri*N[i] + rj*N[j],[mod])
    return N

def add_to_column(M,i,j,ci=1,cj=1,mod=2):
    """
    Replaces column i (of M) with sum ci multiple of ith column and cj multiple of jth column
    
    Parameters
    ----------
    M : np.array
        matrix 
    i : int
        index of column being altered
    j : int
        index of column being added to altered
    ri : int, optional
        Multiplier for ith column
    rj : int, optional
        Multiplier for jth column
    mod : int, optional 
        modular addition to be used

    Returns
    -------
    N : np.array
        copy of M with ith row replaced with sum of multiples of ith row
        and jth row
    """
    N = M.transpose()
    return add_to_row(N,i,j,ci,cj,mod=mod).transpose()

def modmult(M,N,mod=2):
    """
    Matrix multiplication modulo a positive integer
    
    Parameters
    ----------
    M, N : np.array, dtype=int
        M,N must be two dimensional and appropriate dimensions for 
        matrix multiplication
    mod : int
        modulus for modulo operations on elements of product
    
    Returns
    -------
    np.array
    """
    return np.mod(np.matmul(M,N),mod)

def matmulreduce(arr,reverse=False,mod=2):
    """
    Recursively multiples a list of matrices.

    For arr = [arr[0],arr[1],arr[2]...arr[n]] returns product arr[0]arr[1]...arr[n]
    If reverse = True, returns product arr[n]arr[n-1]...arr[0]
    
    Parameters
    ----------
    arr : list of np.array
        list of nxm matrices represented as np.array
    reverse : bool, optional
        order to multiply the matrices
    mod : int, optional
        modulus for modulo operations on elements of products
    
    Returns
    -------
    P : np.array
        Product of matrices in the list
    """

    if reverse:
        items = range(len(arr)-1,-1,-1)
    else:
        items = range(len(arr))
    P = arr[items[0]]
    for i in items[1:]:
        P = modmult(P, arr[i],mod=mod)
    return P
    
def matsumreduce(arr,mod=2):
    """
    Recursively adds a list of matrices.
    
    Parameters
    ----------
    arr : list of np.array
        list of nxm matrices represented as np.array
    mod : int, optional
        modulus for modulo operations on elements of sums
    
    Returns
    -------
    S : np.array
        Sum of matrices in the list
    """    
    S = arr[0]
    for i in range(1,len(arr)):
        S = np.mod(S + arr[i],[mod])
    return S

## Convenience methods for computing Smith Normal Form 
## All of these operations have themselves as inverses 

def _sr(i,j,M,L):
    return swap_rows(i,j,M,L)

def _sc(i,j,M,R):
    return swap_columns(i,j,M,R)

def _ar(i,j,M,L,mod=2):
    return add_to_row(M,i,j,mod=mod),add_to_row(L,i,j,mod=mod)

def _ac(i,j,M,R,mod=2):
    return add_to_column(M,i,j,mod=mod),add_to_column(R,i,j,mod=mod)

def _get_next_pivot(M,s1,s2=None):
    """
    Determines the first r,c indices in the submatrix of M starting
    with row s1 and column s2 index (row,col) that is nonzero, 
    if it exists.

    Search starts with the s2th column and looks for the first nonzero
    s1 row. If none is found, search continues to the next column and so 
    on.
    
    Parameters
    ----------
    M : np.array
        matrix represented as np.array
    s1 : int
        index of row position to start submatrix of M
    s2 : int, optional, default = s1
        index of column position to start submatrix of M
    
    Returns
    -------
    (r,c) : tuple of int or None
        
    """
    # find the next nonzero pivot to put in s,s spot for Smith Normal Form
    m,n = M.shape
    if not s2:
        s2 = s1
    for c in range(s2,n):
        for r in range(s1,m):
            if M[r,c] != 0:
                return (r,c)
    return None

def smith_normal_form_mod2(M,track=False):
    """
    Computes the invertible transformation matrices needed to compute the 
    Smith Normal Form of M modulo 2
    
    Parameters
    ----------
    M : np.array
        a rectangular matrix with elements in $Z_2$
    track : bool
        if track=True will print out the transformation as it 
        discovers L[i] and R[j]
    
    Returns
    -------
    L, R, S, Linv : np.arrays
        LMR = S is the Smith Normal Form of the matrix M. 
    
    Note
    ----
    Given a mxn matrix $M$ with 
    entries in $Z_2$ we start with the equation: $L[0] M R[0] = S$, where 
    $L[0] = I_m$, and $R[0]=I_n$ are identity matrices and $S = M$. We 
    repeatedly multiply the left and right side of the equation by 
    invertible matrices $L[i]$ and $R[j]$ to transform S into a diagonal 
    matrix. At the end we verify the product:
    $$L M R = S.$$
    where $L = L[s]L[s-1]...L[1]L[0]$ and $R = R[0]R[1]...R[t]$.
       
    """

    S = copy.copy(M)
    dimL,dimR = M.shape
    mod = 2
    
    ## initialize left and right transformations with identity matrices
    IL = np.eye(dimL,dtype=int)
    IR = np.eye(dimR,dtype=int)

    L = np.eye(dimL,dtype=int)
    R = np.eye(dimR,dtype=int)    

    Linv = np.eye(dimL,dtype=int)

    if track:
        print(L,'L\n')  
        print(M,'M\n')
        print(R,'R\n')

    for s in range(min(dimL,dimR)):
        print('.'),
        if track:
            print(f'\ns={s}\n')
        ## Find index pair (rdx,cdx) with value 1 in submatrix M[s:,s:] 
        pivot = _get_next_pivot(S,s)
        if not pivot:
            break
        else:
            rdx,cdx = pivot
        if track:
            print(f'/nPivot={rdx},{cdx}')
        ## Swap rows and columns as needed so that 1 is in the s,s position
        if rdx > s:
            S,L = _sr(s,rdx,S,L)
            Linv = swap_columns(s,rdx,Linv)[0]
            if track:
                print(L,f'L\n',S,'S\n',) 
        if cdx > s:
            S,R= _sc(s,cdx,S,R)
            if track:
                print(S,'S\n',R,f'R\n') 

        # add sth row to every row with 1 in sth column & sth column to every column with 1 in sth row
        row_indices = [idx for idx in range(s+1,dimL) if S[idx][s] == 1]
        for rdx in row_indices:
            S,L = _ar(rdx,s,S,L,mod=mod)
            Linv = add_to_column(Linv,s,rdx,mod=mod)
            if track:
                print(L,f'L\n',S,'S\n',) 
        column_indices = [jdx for jdx in range(s+1,dimR) if S[s][jdx] == 1]
        for jdx,cdx in enumerate(column_indices):
            S,R = _ac(cdx,s,S,R)
            if track:
                print(R,f'R\n',S,'S\n',) 
    return L,R,S,Linv

        
def reduced_row_echelon_form_mod2(M,track=False,mod=2):
    """
    Computes the invertible transformation matrices needed to compute 
    the reduced row echelon form of M modulo 2
    
    Parameters
    ----------
    M : np.array
        a rectangular matrix with elements in $Z_2$
    track
        bool
        if track=True will print out the transformation as it 
        discovers L[i] 
    
    Returns
    -------
    L, S, Linv : np.arrays 
        LM = S where S is the reduced echelon form of M
        and M = LinvS    
        
    Note
    ----
    To get the reduced row echelon form for M of dimensions mxn we 
    start with the equation: I(m) M = S,
    where I(m) is the identity matrix and S starts out equal to M.
    We repeatedly multiply the left side of both sides of the equation 
    by invertible matrices 
    L[i] to transform S into reduced row echelon form. At the end we 
    verify the product:
    L[s]L[s-1]...L[0] M = S .    
    """

    S = copy.copy(M)
    dimL,dimR = M.shape
    mod = 2
    
    ## method with numpy
    IL = np.eye(dimL,dtype=int)
    
    Linv = np.eye(dimL,dtype=int)
    L = np.eye(dimL,dtype=int)
    
    if track:
        print(L,'L\n')  
        print(M,'M\n')
    for s2 in range(dimR):
        for s1 in range(s2,dimL):
            ## Find index pair (rdx,cdx) with value 1 in submatrix M[s1:,:]
            ## look for the first 1 in the s2 column
            pivot = _get_next_pivot(S,s1,s2)
            if pivot:
                rdx,cdx = pivot
                s2 = cdx
                if track:
                    print(f'/nPivot={rdx},{cdx}')
                break           
                ## Swap rows as needed so that 1 leads the row
        else:
            continue
        if rdx > s1:
            S,L = _sr(s1,rdx,S,L)
            Linv = swap_columns(rdx,s1,Linv)[0] 
            if track:
                print(L,f'L\n',S,'S\n',) 
        # add sth row to every nonzero row 
        row_indices = [idx for idx in range(dimL) if idx != s1 and S[idx][cdx] == 1]
        for idx in row_indices:
            S,L = _ar(idx,s1,S,L,mod=mod)
            Linv = add_to_column(Linv,s1,idx,mod=mod)
            if track:
                print(L,f'L\n',S,'S\n',) 

    return L,S,Linv

## Private
def _coeff(n):
    '''
    Computes Zmod2 coordinates for elements of an n-dimensional module
    
    Parameters
    ----------
    n : int
        dimension of the space, must be nonnegative
    
    Returns
    -------
    list
        list of np.arrays with entries in Zmod2
    '''

    def addabit(arr):
        temp = list()
        for a in arr:
            temp.append(np.append(a,0))
            temp.append(np.append(a,1))
        return temp
    arr = [np.array([0]),np.array([1])]
    for idx in range(1,n):
        arr = addabit(arr)
    return iter(arr)


def image_group(im2):
    """
    Generate the boundary group
    
    Parameters
    ----------
    im2 : np.array
        columns form a basis for the boundary group
    
    Returns
    -------
     : list
        list of elements of the boundary group
    """
    msg = """
    image_group() provides a very inefficient method for generating the boundary
    group and should only be used for small examples.
    """
    warnings.warn(msg)
    if np.sum(im2) == 0:
        return None
    image_basis = im2.transpose()
    image_group = list()
    for alpha in _coeff(len(image_basis)):
        temp = matsumreduce([a*image_basis[idx] for idx,a in enumerate(alpha)])
        image_group.append(temp)
    return sorted([g for g in image_group],key=lambda g: np.sum(g))

def _coset_reps(bs,image_group,shortest=True):
    """
    Private method to compute the coset of the homology group associated to a cycle. 
    Very inefficient so should only be used on small sets.

    Parameters
    ----------
    bs : np.array
        cycle in chain group
    image_group : list
        list of chains in the boundary group
    shortest : bool, optional
        restricts the answer to the shortest cycles
        in the coset
    
    Returns
    -------
     : list
        cycles in the coset represented by bs
    """
    coset = list()
    for img in image_group:
        coset.append(matsumreduce([img,bs]))
    coset = sorted(coset,key=lambda x: np.sum(x))
    if shortest:
        mincoset = np.sum(coset[0]) 
        shortest_cycles = [g for g in coset if np.sum(g) == mincoset]
        return shortest_cycles
    else:
        return coset

def homology_basis(bd,k,C=None,shortest=False):
    """
    Compute a basis for the kth-homology group with boundary
    matrices given by bd
    
    Parameters
    ----------
    bd : dict
        dict of k-boundary matrices keyed on k
    k : int 
        k must be an integer greater than 0
        bd must have keys for k, and k+1
    C : None or list
        optional, list of k-cells used to interpret the generators
        bd[k] is boundary matrix with rows and columns indexed by
        k-1 and k cells. C is a list of k chains ordered
        to match the column index of bd[k] 

    shortest : bool, optional
        option to look for shortest basis using boundaries
        only good for very small examples

    Returns
    -------
    : list or dict
        list of generators as 0-1 tuples, if C then generators will be 
        k-chains
        if shortest then returns a dictionary of shortest cycles for each coset.
    """
    L1,R1,S1,L1inv = smith_normal_form_mod2(bd[k])
    L2,R2,S2,L2inv = smith_normal_form_mod2(bd[k+1])
    
    rank1 = np.sum(S1); print(f"rank{k} = {rank1}")
    rank2 = np.sum(S2); print(f"rank{k+1} = {rank2}")
    nullity1 = S1.shape[1]-rank1; print(f"nullity{k} = {nullity1}")
    betti1 = S1.shape[1]-rank1 - rank2; print(f"betti{k} = {betti1}")
    cokernel2_dim = S1.shape[1] - rank2; print(f"cokernel{k+1} dimension = {cokernel2_dim}")
    
    ker1 = R1[:,rank1:]
    im2 = L2inv[:,:rank2]
    cokernel2 = L2inv[:,rank2:]
    cokproj2 = L2[rank2:,:]
    
    proj = matmulreduce([cokernel2,cokproj2,ker1]).transpose()
    _,proj,_ = reduced_row_echelon_form_mod2(proj)
    proj = np.array([row for row in proj if np.sum(row)>0])
    print('hom basis reps\n',proj)
    if shortest:
        img_group = image_group(im2)
        if img_group:
            coset = dict()
            for idx,bs in enumerate(proj):
                if C:
                    coset[idx] = interpret(C,_coset_reps(bs,img_group))
                else:
                    coset[idx] = _coset_reps(bs,img_group)
            return coset
        else:
            if C:
                return interpret(C,proj)
            else:
                return proj
    else:
        if C:
            return interpret(C,proj)
        else:
            return proj
    
def hypergraph_homology_basis(h,k,shortest=False):
    """
    Computes the kth-homology group mod 2 for the ASC
    associated with the hypergraph h.
    
    Parameters
    ----------
    h : hnx.Hypergraph

    k : int
        k must be an integer greater than 0

    shortest : bool, optional
        option to look for shortest basis using boundaries
        only good for very small examples   

    Returns
    -------
    : list
        list of generators as k-chains
    """
    max_edge_size = np.max([len(e) for e in h.edges()])
    if k+1 > max_edge_size or k < 1:
        return 'wrong dim'
    C = dict()
    for i in range(k-1,k+2):
        C[i] = kchainbasis(h,i)
    bd = dict()
    for i in range(k,k+2):
        bd[i] = bkMatrix(C[i-1],C[i])


    return homology_basis(bd,k,C=C[k],shortest=shortest)







import numpy as np

def jacobi(A, b, tol=1e-8, max_iter=500):
    n = len(A)
    x = np.zeros(n)
    for k in range(max_iter):
        x_new = np.zeros_like(x)
        for i in range(n):
            s = sum(A[i][j] * x[j] for j in range(n) if j != i)
            x_new[i] = (b[i] - s) / A[i][i]
        if np.linalg.norm(x_new - x, ord=np.inf) < tol:
            return x_new, k+1
        x = x_new
    return x, max_iter

def gauss_seidel(A, b, tol=1e-8, max_iter=500):
    n = len(A)
    x = np.zeros(n)
    for k in range(max_iter):
        x_old = x.copy()
        for i in range(n):
            s1 = sum(A[i][j] * x[j] for j in range(i))
            s2 = sum(A[i][j] * x_old[j] for j in range(i+1, n))
            x[i] = (b[i] - s1 - s2) / A[i][i]
        if np.linalg.norm(x - x_old, ord=np.inf) < tol:
            return x, k+1
    return x, max_iter

# Example
A = [[10, -1, 2, 0],
     [-1, 11, -1, 3],
     [2, -1, 10, -1],
     [0, 3, -1, 8]]
b = [6, 25, -11, 15]

print("Jacobi:", jacobi(A, b))
print("Gauss-Seidel:", gauss_seidel(A, b))

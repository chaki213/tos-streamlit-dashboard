import numpy as np
from scipy.stats import norm

def N(x):
    return norm.cdf(x)

def n(x):
    return norm.pdf(x)

def calculate_charm(S, K, t, rf, d, σ):
    """
    Calculate charm (delta decay) using Black-Scholes model.
    
    Parameters:
    S (float): Current stock price
    K (float): Strike price
    t (float): Time to expiry in years
    rf (float): Risk-free rate
    d (float): Dividend yield
    σ (float): Implied volatility
    
    Returns:
    float: Charm value (daily delta decay)
    """
    if t <= 0:
        return 0
        
    d1 = (np.log(S/K) + (rf - d + 0.5 * σ**2) * t) / (σ * np.sqrt(t))
    d2 = d1 - σ * np.sqrt(t)
    
    charm = d * np.exp(-d * t) * N(d1) - np.exp(-d * t) * n(d1) * ((2 * rf - d) * t - d2 * σ * np.sqrt(t)) / (2 * t * σ * np.sqrt(t))
    
    return charm/365  # Convert to daily charm
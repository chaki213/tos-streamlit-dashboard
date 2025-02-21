import numpy as np
from scipy.stats import norm

def N(x):
    return norm.cdf(x)

def n(x):
    return norm.pdf(x)

def calculate_vanna(S, K, t, rf, d, σ):
    """
    Calculate vanna (delta sensitivity to volatility changes) using Black-Scholes model.
    
    Parameters:
    S (float): Current stock price
    K (float): Strike price
    t (float): Time to expiry in years
    rf (float): Risk-free rate
    d (float): Dividend yield
    σ (float): Implied volatility
    
    Returns:
    float: Vanna value (dDelta/dVol)
    """
    if t <= 0:
        return 0
            
    d1 = (np.log(S/K) + (rf - d + 0.5 * σ**2) * t) / (σ * np.sqrt(t))
    d2 = d1 - σ * np.sqrt(t)
    
    # Vanna is the second-order derivative of the option price with respect to spot and volatility
    # For a call option: -e^(-d*t) * n(d1) * d2 / σ
    vanna = -np.exp(-d * t) * n(d1) * d2 / σ
    
    return vanna
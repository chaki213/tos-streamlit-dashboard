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
    
    # both of these work. is there a difference? 
    # Need differnt equation for call and put?
    charm = -np.exp(-d * t) * (n(d1) * (2 * (rf - d) * t - d2 * σ * np.sqrt(t)) / (2 * t * σ * np.sqrt(t)) + d * N(d1))

    ###
    #charm2 = d * np.exp(-d * t) * N(d1) - np.exp(-d * t) * n(d1) * ((2 * rf - d) * t - d2 * σ * np.sqrt(t)) / (2 * t * σ * np.sqrt(t))
    
    return charm/365   # Convert to daily charm

# Naive Dealer Charm Exposure:
""" formula: (call OI + put OI) × charm × 100 × underlying_price

For calls (dealer long):

OTM calls: Positive charm → dealer buys stock
ITM calls: Negative charm → dealer buys stock


For puts (dealer short):

OTM puts: Positive charm → dealer buys stock
ITM puts: Negative charm → dealer buys stock

The dealer's position (long calls, short puts) combined with the charm effect means
all components work in the same direction, so we ADD the open interest.

This formula will give us the dollar value of stock the dealer needs to buy (positive)
or sell (negative) due to the passage of one day. """
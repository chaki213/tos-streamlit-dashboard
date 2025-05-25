#!/usr/bin/env python3
"""
Black-Scholes Greeks Calculator for Options

Since ThinkorSwim RTD doesn't provide calculated Greeks, this module
computes them using Black-Scholes formulas from available market data.
"""

import math
from typing import Dict, Optional
from datetime import datetime, date
import numpy as np
from scipy.stats import norm

class GreeksCalculator:
    """
    Calculate option Greeks using Black-Scholes model
    """
    
    @staticmethod
    def calculate_time_to_expiry(expiry_date: date) -> float:
        """
        Calculate time to expiry in years
        
        Args:
            expiry_date: Option expiration date
            
        Returns:
            float: Time to expiry in years
        """
        today = datetime.now().date()
        days_to_expiry = (expiry_date - today).days
        
        # Minimum of 1 day to avoid division by zero
        days_to_expiry = max(days_to_expiry, 1)
        
        # Convert to years (using 252 trading days)
        return days_to_expiry / 252.0
    
    @staticmethod
    def estimate_implied_volatility(option_price: float, underlying_price: float, 
                                  strike_price: float, time_to_expiry: float, 
                                  risk_free_rate: float = 0.05, 
                                  is_call: bool = True) -> float:
        """
        Estimate implied volatility using simple approximation
        
        For production use, consider implementing Newton-Raphson method
        """
        if time_to_expiry <= 0 or option_price <= 0:
            return 0.20  # Default 20% volatility
        
        # Simple approximation for ATM options
        if abs(underlying_price - strike_price) / underlying_price < 0.05:
            # ATM approximation: IV ≈ option_price * sqrt(2π) / (underlying_price * sqrt(T))
            return max(0.01, min(3.0, 
                option_price * math.sqrt(2 * math.pi) / 
                (underlying_price * math.sqrt(time_to_expiry))
            ))
        
        # For non-ATM, use iterative approximation
        for vol in np.arange(0.01, 3.0, 0.01):
            bs_price = GreeksCalculator.black_scholes_price(
                underlying_price, strike_price, time_to_expiry, 
                risk_free_rate, vol, is_call
            )
            if abs(bs_price - option_price) < 0.01:
                return vol
        
        return 0.20  # Default fallback
    
    @staticmethod
    def black_scholes_price(S: float, K: float, T: float, r: float, 
                          sigma: float, is_call: bool = True) -> float:
        """
        Calculate Black-Scholes option price
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiry in years
            r: Risk-free rate
            sigma: Volatility
            is_call: True for call, False for put
        """
        if T <= 0 or sigma <= 0:
            return max(0, (S - K) if is_call else (K - S))
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if is_call:
            return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    @staticmethod
    def calculate_delta(S: float, K: float, T: float, r: float, 
                       sigma: float, is_call: bool = True) -> float:
        """
        Calculate option Delta
        
        Delta measures the rate of change of option price with respect to 
        changes in the underlying asset's price.
        """
        if T <= 0 or sigma <= 0:
            return 1.0 if (is_call and S > K) else 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        
        if is_call:
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    
    @staticmethod
    def calculate_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate option Vega
        
        Vega measures the rate of change of option price with respect to 
        changes in the underlying asset's volatility.
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        
        return S * norm.pdf(d1) * math.sqrt(T) / 100  # Divided by 100 for percentage points
    
    @staticmethod
    def calculate_theta(S: float, K: float, T: float, r: float, 
                       sigma: float, is_call: bool = True) -> float:
        """
        Calculate option Theta
        
        Theta measures the rate of change of option price with respect to time.
        Returns theta per day (divided by 365).
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        theta_part1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
        
        if is_call:
            theta_part2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
            theta = theta_part1 + theta_part2
        else:
            theta_part2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
            theta = theta_part1 + theta_part2
        
        return theta / 365  # Convert to daily theta
    
    @classmethod
    def calculate_all_greeks(cls, underlying_price: float, strike_price: float,
                           expiry_date: date, option_price: float = None,
                           risk_free_rate: float = 0.05, 
                           implied_vol: float = None,
                           is_call: bool = True) -> Dict[str, float]:
        """
        Calculate all Greeks for an option
        
        Args:
            underlying_price: Current price of underlying asset
            strike_price: Option strike price
            expiry_date: Option expiration date
            option_price: Current option price (for IV estimation if needed)
            risk_free_rate: Risk-free interest rate (default 5%)
            implied_vol: Implied volatility (if None, will estimate from option_price)
            is_call: True for call option, False for put
            
        Returns:
            dict: Dictionary containing calculated Greeks
        """
        time_to_expiry = cls.calculate_time_to_expiry(expiry_date)
        
        # Estimate IV if not provided
        if implied_vol is None:
            if option_price is not None and option_price > 0:
                implied_vol = cls.estimate_implied_volatility(
                    option_price, underlying_price, strike_price, 
                    time_to_expiry, risk_free_rate, is_call
                )
            else:
                # Use historical volatility approximation for SPY (~20%)
                implied_vol = 0.20
        
        # Ensure valid parameters
        if time_to_expiry <= 0 or implied_vol <= 0:
            return {
                'delta': 0.0,
                'vega': 0.0,
                'theta': 0.0,
                'implied_vol': implied_vol
            }
        
        try:
            delta = cls.calculate_delta(underlying_price, strike_price, 
                                      time_to_expiry, risk_free_rate, 
                                      implied_vol, is_call)
            
            vega = cls.calculate_vega(underlying_price, strike_price, 
                                    time_to_expiry, risk_free_rate, implied_vol)
            
            theta = cls.calculate_theta(underlying_price, strike_price, 
                                      time_to_expiry, risk_free_rate, 
                                      implied_vol, is_call)
            
            return {
                'delta': delta,
                'vega': vega,
                'theta': theta,
                'implied_vol': implied_vol
            }
            
        except Exception as e:
            print(f"Error calculating Greeks: {e}")
            return {
                'delta': 0.0,
                'vega': 0.0,
                'theta': 0.0,
                'implied_vol': 0.20
            } 
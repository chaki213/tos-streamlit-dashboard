import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from scipy import interpolate

class VolatilitySurfaceBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty surface chart"""
        fig = go.Figure()
        self._set_layout(fig)
        return fig

    def create_chart(self, data: dict, strikes: list, expirations: list, option_symbols: list) -> go.Figure:
        """Build and return the volatility surface chart"""
        fig = go.Figure()
        
        # Get current price
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()

        # Create mesh grid for surface
        strike_grid = np.array(strikes)
        
        # Create evenly spaced indices for expirations instead of timestamps
        expiry_datetimes = [datetime.strptime(exp, '%y%m%d') for exp in expirations]
        expiry_indices = np.arange(len(expiry_datetimes))
        X, Y = np.meshgrid(strike_grid, expiry_indices)
        Z_calls = np.full_like(X, np.nan, dtype=np.float64)  # Initialize with NaN instead of zeros
        Z_puts = np.full_like(X, np.nan, dtype=np.float64)   # Initialize with NaN instead of zeros

        # Calculate date labels and create a text_data array (as plain Python lists)
        date_labels = [dt.strftime('%m-%d-%y') for dt in expiry_datetimes]
        # Use text_data instead of customdata
        text_data = [[date for _ in strikes] for date in date_labels]

        print("text_data: ", text_data)
        customdata = text_data

        
        # Fill volatility values and interpolate missing data
        for i, expiry in enumerate(expirations):
            for j, strike in enumerate(strikes):
                # Look up both call and put symbols
                call_sym = next((s for s in option_symbols if f'{expiry}C{strike}' in s), None)
                put_sym = next((s for s in option_symbols if f'{expiry}P{strike}' in s), None)
                
                # Get implied vol values, use NaN for missing or zero values
                call_vol = float(data.get(f"{call_sym}:IMPL_VOL", 0) or 0)
                put_vol = float(data.get(f"{put_sym}:IMPL_VOL", 0) or 0)
                
                Z_calls[i,j] = call_vol if call_vol > 0 else np.nan
                Z_puts[i,j] = put_vol if put_vol > 0 else np.nan

        # Interpolate missing values for each expiry
        for i in range(Z_calls.shape[0]):
            # Handle calls
            mask = ~np.isnan(Z_calls[i])
            if np.any(mask):
                x = strike_grid[mask]
                y = Z_calls[i][mask]
                if len(x) > 3:  # Need at least 4 points for cubic interpolation
                    f = interpolate.interp1d(x, y, kind='cubic', fill_value='extrapolate')
                    Z_calls[i] = f(strike_grid)
            
            # Handle puts
            mask = ~np.isnan(Z_puts[i])
            if np.any(mask):
                x = strike_grid[mask]
                y = Z_puts[i][mask]
                if len(x) > 3:
                    f = interpolate.interp1d(x, y, kind='cubic', fill_value='extrapolate')
                    Z_puts[i] = f(strike_grid)

        # Updated surface properties for smoother interpolation
        surface_properties = dict(
            colorscale=[
                [0, 'rgb(0,0,130)'],
                [0.25, 'rgb(0,255,255)'],
                [0.5, 'rgb(0,255,0)'],
                [0.75, 'rgb(255,255,0)'],
                [1, 'rgb(255,0,0)']
            ],
            colorbar=dict(
                title=dict(
                    text='IV %',
                    side='right'
                ),
                tickfont=dict(color='white'),
                title_font=dict(color='white')
            ),
            lighting=dict(
                #ambient=0.85,    # Increased ambient light further
                #diffuse=0.95,    # Increased diffuse light further
                #fresnel=0.1,     # Reduced fresnel for smoother look
                #roughness=0.2,   # Further reduced roughness
                #specular=0.3     # Reduced specular """
                ambient=0.6,
                diffuse=0.8,
                fresnel=0.2,
                roughness=0.5,
                specular=0.5
            ),
            contours=dict(
                x=dict(show=True, color='rgb(150,150,150)', width=1),
                y=dict(show=True, color='rgb(150,150,150)', width=1),
                z=dict(show=True, color='rgb(150,150,150)', width=1) 
            ),
            connectgaps=True,     # Connect gaps between missing values
            surfacecolor=None,    # Let plotly handle the coloring
            showscale=True,
            opacity=0.92,         # Slightly increased opacity
        )

        # Add call surface using the text attribute for expiration dates.
        call_surface = go.Surface(
            x=X,
            y=Y,
            z=Z_calls,
            text=text_data,  # pass expiration dates using text
            customdata=customdata,
            hovertemplate=(
                "Strike: $%{x:.2f}<br>" +
                "IV: %{z:.2f}%<br>" +
                "<extra></extra>"
            ),
            name='Calls',
            visible=True,
            **surface_properties
        )

        # Add put surface similarly.
        put_surface = go.Surface(
            x=X,
            y=Y,
            z=Z_puts,
            text=text_data,
            customdata=customdata,
            hovertemplate=(
                "Strike: $%{x:.2f}<br>" +
                "IV: %{z:.2f}%<br>" +
                "<extra></extra>"
            ),
            name='Puts',
            visible=False,
            **surface_properties
        )

        fig.add_trace(call_surface)
        fig.add_trace(put_surface)

        self._set_layout(fig, current_price, expiry_datetimes)
        return fig

    def _set_layout(self, fig, current_price=None, expiry_dates=None):
        price_str = f" (Current Price: ${current_price:.2f})" if current_price else ""
        
        # Create date labels if dates are provided
        if expiry_dates:
            date_labels = [dt.strftime('%m-%d-%y') for dt in expiry_dates]
            indices = list(range(len(date_labels)))
        else:
            date_labels = []
            indices = []
        
        # Create camera preset buttons and option type toggle
        updatemenus = [
            dict(
                type='buttons',
                showactive=False,
                buttons=[
                    dict(
                        label='Side View (Smile)',
                        method='relayout',
                        args=[{'scene.camera': dict(
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=0, y=0, z=-0.1),
                            eye=dict(x=2, y=-2, z=1.5)
                        )}]
                    ),
                    dict(
                        label='Top View',
                        method='relayout',
                        args=[{'scene.camera': dict(
                            up=dict(x=0, y=1, z=0),
                            center=dict(x=0, y=0, z=0),
                            eye=dict(x=0, y=0, z=2.5)
                        )}]
                    ),
                    dict(
                        label='Term Structure',
                        method='relayout',
                        args=[{'scene.camera': dict(
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=0, y=0, z=0),
                            eye=dict(x=0, y=2.5, z=1)
                        )}]
                    )
                ],
                direction='down',
                pad={'r': 10, 't': 10},
                x=0.9,
                xanchor='right',
                y=1.1,
                yanchor='top',
                bgcolor='rgb(50,50,50)',
                font=dict(color='white')
            ),
            # Add option type toggle
            dict(
                type='buttons',
                showactive=True,
                buttons=[
                    dict(
                        label='Calls',
                        method='update',
                        args=[{'visible': [True, False]},
                              {'title': f'{self.symbol} Call Options Implied Volatility Surface{price_str}'}]
                    ),
                    dict(
                        label='Puts',
                        method='update',
                        args=[{'visible': [False, True]},
                              {'title': f'{self.symbol} Put Options Implied Volatility Surface{price_str}'}]
                    )
                ],
                direction='down',
                pad={'r': 10, 't': 10},
                x=0.8,  # Position to the left of the camera buttons
                xanchor='right',
                y=1.1,
                yanchor='top',
                bgcolor='rgb(50,50,50)',
                font=dict(color='white')
            )
        ]
        
        fig.update_layout(
            title=dict(
                text=f'{self.symbol} Call Options Implied Volatility Surface{price_str}',
                x=0.5,
                xanchor='center',
                font=dict(size=20, color='white')
            ),
            updatemenus=updatemenus,
            scene=dict(
                xaxis=dict(
                    title='Strike Price',
                    gridcolor='rgb(50,50,50)',
                    showbackground=True,
                    backgroundcolor='rgb(0,0,0)',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white'),
                    color='white'
                ),
                yaxis=dict(
                    title='Expiration',
                    ticktext=date_labels,
                    tickvals=indices,
                    gridcolor='rgb(50,50,50)',
                    showbackground=True,
                    backgroundcolor='rgb(0,0,0)',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white'),
                    color='white'
                ),
                zaxis=dict(
                    title='Implied Volatility %',
                    gridcolor='rgb(50,50,50)',
                    showbackground=True,
                    backgroundcolor='rgb(0,0,0)',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white'),
                    color='white'
                ),
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=-0.1),
                    eye=dict(x=2, y=-2, z=1.5)
                ),
                bgcolor='rgb(0,0,0)'
            ),
            height=700,
            margin=dict(t=80, b=0, l=0, r=0),
            plot_bgcolor='rgb(0,0,0)',
            paper_bgcolor='rgb(0,0,0)'
        )
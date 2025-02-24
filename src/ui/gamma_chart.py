import plotly.graph_objects as go
import numpy as np

class GammaChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # Store previous price for change calculation
        self.previous_price = None
        # Dark theme color scheme with high contrast colors
        self.colors = {
            'positive': 'rgb(0, 255, 127)',  # Bright green
            'negative': 'rgb(255, 105, 97)',  # Bright red
            'neutral': 'rgb(220, 220, 220)',  # Light gray
            'price_line': 'rgb(102, 204, 255)',  # Bright blue
            'zero_line': 'rgb(255, 255, 255)',  # White
            'background': 'rgb(17, 17, 17)',  # Almost black but not too dark
            'plot_bg': 'rgb(30, 30, 30)',  # Lighter background for plot area
            'grid': 'rgb(100, 100, 100)',  # Medium gray for grid
            'text': 'rgb(255, 255, 255)'  # White text
        }
        # Theme configurations
        self.theme = {
            'font_family': 'Arial, sans-serif',
            'title_font_size': 18,
            'axis_font_size': 12,
            'label_font_size': 12,
            'legend_font_size': 12
        }

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart with improved styling for dark theme"""
        fig = go.Figure()
        
        fig.update_layout(
            template='plotly_dark',
            title={
                'text': f'{self.symbol} Gamma Exposure - Waiting for data...',
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['title_font_size'],
                    'color': self.colors['text']
                },
                'x': 0.01,
                'xanchor': 'left',
                'y': 0.95,
                'yanchor': 'top',
            },
            xaxis_title={
                'text': 'Gamma Exposure ($M)',
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['axis_font_size'],
                    'color': self.colors['text']
                }
            },
            yaxis_title={
                'text': 'Strike Price',
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['axis_font_size'],
                    'color': self.colors['text']
                }
            },
            height=600,
            margin={'l': 60, 'r': 30, 't': 80, 'b': 50},
            plot_bgcolor=self.colors['plot_bg'],
            paper_bgcolor=self.colors['background'],
            hovermode='closest',
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['legend_font_size'],
                    'color': self.colors['text']
                }
            }
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridcolor=self.colors['grid'],
            zeroline=True,
            zerolinecolor=self.colors['zero_line'],
            zerolinewidth=2,
            color=self.colors['text']
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self.colors['grid'],
            color=self.colors['text']
        )
        
        # Add placeholder annotation
        fig.add_annotation(
            text="Start data collection to view gamma exposure",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={'size': 16, 'color': self.colors['text']}
        )
        
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the gamma exposure chart with enhanced visuals for dark theme"""
        # Create base figure with custom styling
        fig = go.Figure()
        
        # Get current price first
        try:
            current_price = float(data.get(f"{self.symbol}:LAST", 0))
            
            # Calculate price change percentage for metrics
            if self.previous_price and self.previous_price > 0:
                price_change = current_price - self.previous_price
                price_change_pct = (price_change / self.previous_price) * 100
                # Store in session state for metrics display
                import streamlit as st
                st.session_state.price_change_pct = f"{price_change_pct:.2f}%"
            
            # Update previous price for next comparison
            self.previous_price = current_price
        except (ValueError, TypeError):
            current_price = 0
            
        if current_price == 0:
            return self.create_empty_chart()
            
        # Calculate GEX values and add to chart
        pos_gex_values, neg_gex_values = self._calculate_gex_values(data, strikes, option_symbols)
        
        # Get min and max gex to center the axis
        max_pos = max(pos_gex_values) if pos_gex_values else 0
        min_neg = min(neg_gex_values) if neg_gex_values else 0
        
        # Take the larger absolute value to ensure symmetry
        max_abs = max(abs(max_pos), abs(min_neg))
        # Add 10% padding
        max_abs = max_abs * 1.1
        
        # Chart type selection based on session state
        import streamlit as st
        chart_type = st.session_state.get('chart_type', 'Horizontal Bars')
        chart_height = st.session_state.get('chart_height', 600)
        
        if chart_type == "Horizontal Bars":
            self._create_horizontal_bar_chart(fig, pos_gex_values, neg_gex_values, strikes)
        elif chart_type == "Vertical Bars":
            self._create_vertical_bar_chart(fig, pos_gex_values, neg_gex_values, strikes)
        else:  # Area chart
            self._create_area_chart(fig, pos_gex_values, neg_gex_values, strikes)
        
        # Add price indicator line
        self._add_price_line(fig, current_price, chart_type)
        
        # Calculate and store key metrics
        self._calculate_and_store_metrics(pos_gex_values, neg_gex_values, strikes)
        
        # Enhance layout with custom styling and centered x-axis
        self._set_enhanced_layout(fig, current_price, chart_height, chart_type, -max_abs, max_abs)
        
        return fig
        
    def _create_horizontal_bar_chart(self, fig, pos_gex_values, neg_gex_values, strikes):
        """Create horizontal bar chart visualization with maximum visibility"""
        # Positive GEX bars
        fig.add_trace(go.Bar(
            x=pos_gex_values,
            y=strikes,
            orientation='h',
            name='Positive GEX',
            marker=dict(
                color=self.colors['positive'],
                line=dict(width=1, color='rgba(255, 255, 255, 0.7)')  # Strong white border
            ),
            opacity=1.0,  # Full opacity
            hovertemplate='Strike: $%{y}<br>GEX: +$%{x:.2f}M<extra></extra>'
        ))
        
        # Negative GEX bars
        fig.add_trace(go.Bar(
            x=neg_gex_values,
            y=strikes,
            orientation='h',
            name='Negative GEX',
            marker=dict(
                color=self.colors['negative'],
                line=dict(width=1, color='rgba(255, 255, 255, 0.7)')  # Strong white border
            ),
            opacity=1.0,  # Full opacity
            hovertemplate='Strike: $%{y}<br>GEX: %{x:.2f}M<extra></extra>'
        ))
        
    def _create_vertical_bar_chart(self, fig, pos_gex_values, neg_gex_values, strikes):
        """Create vertical bar chart visualization with maximum visibility"""
        # Positive GEX bars
        fig.add_trace(go.Bar(
            y=pos_gex_values,
            x=strikes,
            name='Positive GEX',
            marker=dict(
                color=self.colors['positive'],
                line=dict(width=1, color='rgba(255, 255, 255, 0.7)')  # Strong white border
            ),
            opacity=1.0,  # Full opacity
            hovertemplate='Strike: $%{x}<br>GEX: +$%{y:.2f}M<extra></extra>'
        ))
        
        # Negative GEX bars
        fig.add_trace(go.Bar(
            y=neg_gex_values,
            x=strikes,
            name='Negative GEX',
            marker=dict(
                color=self.colors['negative'],
                line=dict(width=1, color='rgba(255, 255, 255, 0.7)')  # Strong white border
            ),
            opacity=1.0,  # Full opacity
            hovertemplate='Strike: $%{x}<br>GEX: %{y:.2f}M<extra></extra>'
        ))
        
    def _create_area_chart(self, fig, pos_gex_values, neg_gex_values, strikes):
        """Create area chart visualization with maximum visibility"""
        # Combine positive and negative values
        combined_values = [p + n for p, n in zip(pos_gex_values, neg_gex_values)]
        
        # Net GEX line
        fig.add_trace(go.Scatter(
            x=strikes,
            y=combined_values,
            mode='lines',
            name='Net GEX',
            line=dict(color=self.colors['price_line'], width=4),  # Thicker line
            hovertemplate='Strike: $%{x}<br>Net GEX: $%{y:.2f}M<extra></extra>'
        ))
        
        # Positive fill
        positive_fill = [max(0, v) for v in combined_values]
        fig.add_trace(go.Scatter(
            x=strikes,
            y=positive_fill,
            mode='none',
            name='Positive GEX',
            fill='tozeroy',
            fillcolor=f'rgba(0, 255, 127, 0.7)',  # Higher opacity
            hoverinfo='skip'
        ))
        
        # Negative fill
        negative_fill = [min(0, v) for v in combined_values]
        fig.add_trace(go.Scatter(
            x=strikes,
            y=negative_fill,
            mode='none',
            name='Negative GEX',
            fill='tozeroy',
            fillcolor=f'rgba(255, 105, 97, 0.7)',  # Higher opacity
            hoverinfo='skip'
        ))
        
        # Zero line - make it more visible
        fig.add_shape(
            type="line", 
            x0=min(strikes), 
            y0=0, 
            x1=max(strikes), 
            y1=0,
            line=dict(color=self.colors['zero_line'], width=2, dash="solid")
        )

    def _add_price_line(self, fig, current_price, chart_type):
        """Add current price indicator line with improved styling"""
        if chart_type == "Horizontal Bars":
            # Horizontal price line for horizontal bar chart
            fig.add_hline(
                y=current_price,
                line=dict(color=self.colors['price_line'], width=3, dash="solid"),
                annotation=dict(
                    text=f"Current Price: ${current_price:.2f}",
                    font=dict(color=self.colors['price_line'], size=14, family="Arial Black"),
                    bgcolor="rgba(0, 0, 0, 0.8)",  # Dark background for contrast
                    bordercolor=self.colors['price_line'],
                    borderwidth=2,
                    borderpad=5
                ),
                annotation_position="top right"
            )
        else:
            # Vertical price line for vertical or area charts
            fig.add_vline(
                x=current_price,
                line=dict(color=self.colors['price_line'], width=3, dash="solid"),
                annotation=dict(
                    text=f"Current Price: ${current_price:.2f}",
                    font=dict(color=self.colors['price_line'], size=14, family="Arial Black"),
                    bgcolor="rgba(0, 0, 0, 0.8)",  # Dark background for contrast
                    bordercolor=self.colors['price_line'],
                    borderwidth=2,
                    borderpad=5
                ),
                annotation_position="top"
            )

    def _calculate_and_store_metrics(self, pos_gex_values, neg_gex_values, strikes):
        """Calculate important metrics and store them for display"""
        import streamlit as st
        
        # Total GEX values
        total_pos_gex = sum(pos_gex_values) / 1000000
        total_neg_gex = sum(neg_gex_values) / 1000000
        
        # Find max values and their strikes
        max_pos_idx = pos_gex_values.index(max(pos_gex_values)) if any(pos_gex_values) else -1
        max_neg_idx = neg_gex_values.index(min(neg_gex_values)) if any(neg_gex_values) else -1
        
        max_pos_strike = strikes[max_pos_idx] if max_pos_idx >= 0 else 0
        max_neg_strike = strikes[max_neg_idx] if max_neg_idx >= 0 else 0
        
        max_pos_gex = max(pos_gex_values) / 1000000 if pos_gex_values else 0
        max_neg_gex = min(neg_gex_values) / 1000000 if neg_gex_values else 0
        
        # Store values in session state for metrics display
        st.session_state.total_pos_gex = total_pos_gex
        st.session_state.total_neg_gex = total_neg_gex
        st.session_state.max_pos_gex = max_pos_gex
        st.session_state.max_pos_strike = max_pos_strike
        st.session_state.max_neg_gex = max_neg_gex
        st.session_state.max_neg_strike = max_neg_strike

    def _set_enhanced_layout(self, fig, current_price, chart_height, chart_type, x_min=None, x_max=None):
        """Apply enhanced layout settings to the chart with centered x-axis and better visibility"""
        # Format title information with key metrics
        import streamlit as st
        gex_totals = ""
        if hasattr(st.session_state, 'total_pos_gex'):
            total_pos = st.session_state.total_pos_gex
            total_neg = st.session_state.total_neg_gex
            gex_totals = f'<span style="color: {self.colors["positive"]}">+${total_pos:.2f}M</span> | <span style="color: {self.colors["negative"]}">${total_neg:.2f}M</span>'
            
        title_text = f'{self.symbol} Gamma Exposure ($ per 1% move)'
        subtitle_text = f'<span style="font-size: 14px; color: {self.colors["text"]}">Net GEX: {gex_totals}</span>'
        
        # Configure axes based on chart type with improved visibility
        if chart_type == "Horizontal Bars":
            # Center the x-axis around zero
            fig.update_layout(
                xaxis=dict(
                    title="Gamma Exposure ($M)",
                    zeroline=True,
                    zerolinecolor=self.colors['zero_line'],
                    zerolinewidth=2,
                    showgrid=True,
                    gridcolor=self.colors['grid'],
                    color=self.colors['text'],
                    range=[x_min, x_max] if x_min is not None and x_max is not None else None,
                    tickfont=dict(size=13, color=self.colors['text']),
                ),
                yaxis=dict(
                    title="Strike Price",
                    showgrid=True,
                    gridcolor=self.colors['grid'],
                    color=self.colors['text'],
                    tickfont=dict(size=13, color=self.colors['text']),
                ),
                barmode='overlay'
            )
        else:
            fig.update_layout(
                xaxis=dict(
                    title="Strike Price",
                    showgrid=True,
                    gridcolor=self.colors['grid'],
                    color=self.colors['text'],
                    tickfont=dict(size=13, color=self.colors['text']),
                ),
                yaxis=dict(
                    title="Gamma Exposure ($M)",
                    zeroline=True,
                    zerolinecolor=self.colors['zero_line'],
                    zerolinewidth=2,
                    showgrid=True,
                    gridcolor=self.colors['grid'],
                    color=self.colors['text'],
                    range=[x_min, x_max] if x_min is not None and x_max is not None else None,
                    tickfont=dict(size=13, color=self.colors['text']),
                )
            )
        
        # Apply final layout settings with improved visibility
        fig.update_layout(
            title={
                'text': f"{title_text}<br>{subtitle_text}",
                'x': 0.01,
                'y': 0.95,
                'xanchor': 'left',
                'yanchor': 'top',
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['title_font_size'],
                    'color': self.colors['text']
                }
            },
            height=chart_height,
            margin={'l': 60, 'r': 30, 't': 100, 'b': 50},
            plot_bgcolor=self.colors['plot_bg'],
            paper_bgcolor=self.colors['background'],
            hovermode='closest',
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {
                    'family': self.theme['font_family'],
                    'size': self.theme['legend_font_size'] + 1,  # Slightly larger
                    'color': self.colors['text']
                },
                'bgcolor': 'rgba(0, 0, 0, 0.7)',  # Black background with transparency
                'bordercolor': 'rgba(255, 255, 255, 0.5)',
                'borderwidth': 1
            }
        )
        
        return fig

    def _calculate_gex_values(self, data, strikes, option_symbols):
        """Calculate positive and negative gamma exposure values"""
        pos_gex_values = []
        neg_gex_values = []
        
        try:
            underlying_price = float(data.get(f"{self.symbol}:LAST", 0))
        except (ValueError, TypeError):
            underlying_price = 0
            
        if underlying_price == 0:
            return [], []
        
        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
                
                # Safely get and convert values, defaulting to 0 if any errors
                try:
                    call_gamma = float(data.get(f"{call_symbol}:GAMMA", 0))
                except (ValueError, TypeError):
                    call_gamma = 0
                    
                try:
                    put_gamma = float(data.get(f"{put_symbol}:GAMMA", 0))
                except (ValueError, TypeError):
                    put_gamma = 0
                    
                try:
                    call_oi = float(data.get(f"{call_symbol}:OPEN_INT", 0))
                except (ValueError, TypeError):
                    call_oi = 0
                    
                try:
                    put_oi = float(data.get(f"{put_symbol}:OPEN_INT", 0))
                except (ValueError, TypeError):
                    put_oi = 0
                
                # gamma exposure per 1% change in the underlying price
                gex = ((call_oi*call_gamma) - (put_oi*put_gamma)) * 100 * (underlying_price*underlying_price) * .01

            except Exception as e:
                # If anything goes wrong with this strike, use 0
                import streamlit as st
                if not hasattr(st.session_state, 'debug_mode') or st.session_state.debug_mode:
                    print(f"Error calculating GEX strike: {strike}")
                gex = 0
            
            if gex > 0:
                pos_gex_values.append(gex)
                neg_gex_values.append(0)
            else:
                pos_gex_values.append(0)
                neg_gex_values.append(gex)
        
        return pos_gex_values, neg_gex_values
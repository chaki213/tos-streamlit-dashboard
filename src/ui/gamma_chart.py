import plotly.graph_objects as go
from src.utils.greeks_calculator import GreeksCalculator
from datetime import date

class GammaChartBuilder:
    def __init__(self, symbol: str, expiry_date: date = None):
        self.symbol = symbol
        self.expiry_date = expiry_date
        self.greeks_calculator = GreeksCalculator()

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = go.Figure()
        self._set_layout(fig, 1, None, "Gamma Exposure", "($ per 1% move)", [], [])  # Use correct parameters
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list, show_vanna: bool = False, show_charm: bool = False) -> go.Figure:
        """Build and return the chart with gamma, vanna, or charm exposure"""
        fig = go.Figure()
        
        # Get current price first
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()
        
        # Determine which chart type to display
        if show_vanna and not show_charm:
            # Show vanna exposure chart
            pos_values, neg_values = self._calculate_vanna_exposure_values(data, strikes, option_symbols)
            chart_title = "Vanna Exposure"
            chart_subtitle = "($ per 1% vol move)"
        elif show_charm and not show_vanna:
            # Show charm exposure chart  
            pos_values, neg_values = self._calculate_charm_exposure_values(data, strikes, option_symbols)
            chart_title = "Charm Exposure"
            chart_subtitle = "($ per day)"
        else:
            # Show gamma exposure chart (default)
            pos_values, neg_values = self._calculate_gex_values(data, strikes, option_symbols)
            chart_title = "Gamma Exposure"
            chart_subtitle = "($ per 1% move)"

        # Find max values and their strikes
        max_pos_idx = pos_values.index(max(pos_values)) if any(pos_values) else -1
        max_neg_idx = neg_values.index(min(neg_values)) if any(neg_values) else -1
        
        max_pos_strike = strikes[max_pos_idx] if max_pos_idx >= 0 else None
        max_neg_strike = strikes[max_neg_idx] if max_neg_idx >= 0 else None
        
        # Fixed max value calculation with safety checks
        max_pos = max(pos_values) if pos_values else 0
        min_neg = min(neg_values) if neg_values else 0
        max_abs_value = max(abs(min_neg), abs(max_pos))
        
        # Ensure we have a non-zero range
        if max_abs_value == 0:
            max_abs_value = 1
            
        # Add padding to the range (30% on each side)
        padding = max_abs_value * 0.3
        chart_range = max_abs_value + padding
        
        # Add the bar traces
        self._add_traces(fig, pos_values, neg_values, strikes, chart_title)
        
        self._add_annotations(
            fig, max_pos, min_neg, padding,
            max_pos_idx, max_pos_strike, max_neg_idx, max_neg_strike,
            current_price, strikes
        )

        self._set_layout(fig, chart_range, current_price, chart_title, chart_subtitle, pos_values, neg_values)
        
        return fig

    def _calculate_gex_values(self, data, strikes, option_symbols):
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
                #print(f"Call: {call_symbol}")
                
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
                
                # gamma exposure per $1 change in the underlying price
                # gex = ((call_oi*call_gamma) - (put_oi*put_gamma)) * 100 * underlying_price

                # gamma exposure per 1% change in the underlying price
                gex = ((call_oi*call_gamma) - (put_oi*put_gamma)) * 100 * (underlying_price*underlying_price) * .01

            except Exception:
                # If anything goes wrong with this strike, use 0
                print(f"Error calculating GEX strike: {strike}")
                gex = 0
            
            if gex > 0:
                pos_gex_values.append(gex)
                neg_gex_values.append(0)
            else:
                pos_gex_values.append(0)
                neg_gex_values.append(gex)
        
        #print("pos_gex_values: ", pos_gex_values)
        #print("neg_gex_values: ", neg_gex_values)
        return pos_gex_values, neg_gex_values

    def _add_traces(self, fig, pos_values, neg_values, strikes, chart_title):
        # Set colors and names based on chart type
        if "Vanna" in chart_title:
            pos_color = 'purple'
            neg_color = 'mediumpurple'
            pos_name = 'Positive Vanna'
            neg_name = 'Negative Vanna'
        elif "Charm" in chart_title:
            pos_color = 'orange'
            neg_color = 'darkorange'
            pos_name = 'Positive Charm'
            neg_name = 'Negative Charm'
        else:
            pos_color = 'green'
            neg_color = 'red'
            pos_name = 'Positive GEX'
            neg_name = 'Negative GEX'
            
        fig.add_trace(go.Bar(
            x=pos_values,
            y=strikes,
            orientation='h',
            name=pos_name,
            marker_color=pos_color
        ))
        
        fig.add_trace(go.Bar(
            x=neg_values,
            y=strikes,
            orientation='h',
            name=neg_name,
            marker_color=neg_color
        ))

    def _add_annotations(self, fig, max_pos, min_neg, padding, max_pos_idx, max_pos_strike, max_neg_idx, max_neg_strike, current_price, strikes):
        # Adjust annotation positions based on padding
        annotation_offset = padding * 0.7  # 70% of padding for annotation offset
        
        # Add horizontal line for current price
        fig.add_hline(
            y=current_price,
            line_color="blue",
            line_width=2
        )
        
        # Add annotations for max values with adjusted positions
        if max_pos_idx >= 0 and max_pos > 0:
            # Value annotation on the right side of positive bar
            fig.add_annotation(
                x=max_pos,
                y=max_pos_strike,
                text=f"+${round(max_pos/1000000)}M",
                showarrow=True,
                arrowhead=2,
                ax=min(40, annotation_offset * 30),
                ay=0,
                align="left"
            )
            # Strike annotation on the left side of positive bar
            fig.add_annotation(
                x=0,  # Position at zero line
                y=max_pos_strike,
                text=f"Strike: {max_pos_strike}",
                showarrow=False,
                xanchor="right",
                xshift=-10  # Shift slightly left of the zero line
            )
        
        if max_neg_idx >= 0 and min_neg < 0:
            # Value annotation on the left side of negative bar
            fig.add_annotation(
                x=min_neg,
                y=max_neg_strike,
                text=f"-${abs(round(min_neg/1000000))}M",
                showarrow=True,
                arrowhead=2,
                ax=max(-40, -annotation_offset * 30),
                ay=0,
                align="right"
            )
            # Strike annotation on the right side of negative bar
            fig.add_annotation(
                x=0,  # Position at zero line
                y=max_neg_strike,
                text=f"Strike: {max_neg_strike}",
                showarrow=False,
                xanchor="left",
                xshift=10  # Shift slightly right of the zero line
            )

    def _set_layout(self, fig, chart_range, current_price=None, chart_title=None, chart_subtitle=None, pos_values=None, neg_values=None):
        price_str = f" Price: ${current_price:.2f}" if current_price else ""
        
        # Calculate totals from the values
        totals_str = ""
        if pos_values and neg_values:
            try:
                total_pos = sum(pos_values)/1000000
                total_neg = sum(neg_values)/1000000
                
                # Color code based on chart type
                if chart_title and "Vanna" in chart_title:
                    totals_str = (f'<span style="color: purple">+${total_pos:.0f}M</span> | '
                                f'<span style="color: mediumpurple">${total_neg:.0f}M</span>')
                elif chart_title and "Charm" in chart_title:
                    totals_str = (f'<span style="color: orange">+${total_pos:.0f}M</span> | '
                                f'<span style="color: darkorange">${total_neg:.0f}M</span>')
                else:
                    totals_str = (f'<span style="color: green">+${total_pos:.0f}M</span> | '
                                f'<span style="color: red">${total_neg:.0f}M</span>')
            except (IndexError, AttributeError):
                pass
        
        # Build title 
        display_title = f"{self.symbol} {chart_title or 'Gamma Exposure'}"
        if chart_subtitle:
            display_title += f" {chart_subtitle}"
        display_title += f"   {price_str}"
        
        # Determine x-axis title based on chart type
        if chart_title and "Vanna" in chart_title:
            x_axis_title = "Vanna Exposure ($M)"
        elif chart_title and "Charm" in chart_title:
            x_axis_title = "Charm Exposure ($M)"
        else:
            x_axis_title = "Gamma Exposure ($M)"
        
        # Add more spacing with &nbsp; HTML entities
        layout_config = {
            'title': {
                'text': (f'{display_title}'
                        f'<span style="float: right">&nbsp;&nbsp;&nbsp;&nbsp;{totals_str}</span>'),
                'xanchor': 'left',
                'x': 0,
                'xref': 'paper',
                'yref': 'paper',
                'font': {'size': 16}
            },
            'xaxis_title': x_axis_title,
            'yaxis_title': 'Strike Price',
            'barmode': 'overlay',
            'showlegend': True,  # Enable legend
            'legend': dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            'height': 600,
            'xaxis': dict(
                range=[-chart_range, chart_range],  # Use padded range
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='black',
            )
        }
        
        fig.update_layout(**layout_config)

    def _calculate_vanna_exposure_values(self, data, strikes, option_symbols):
        """Calculate vanna exposure values for histogram display"""
        pos_vanna_values = []
        neg_vanna_values = []
        
        try:
            underlying_price = float(data.get(f"{self.symbol}:LAST", 0))
        except (ValueError, TypeError):
            underlying_price = 0
            
        if underlying_price == 0:
            return [], []
        
        non_zero_count = 0
        
        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
                
                # Get RTD values first
                try:
                    call_vega = float(data.get(f"{call_symbol}:VEGA", 0))
                    call_delta = float(data.get(f"{call_symbol}:DELTA", 0))
                    call_oi = float(data.get(f"{call_symbol}:OPEN_INT", 0))
                    call_price = float(data.get(f"{call_symbol}:LAST", 0))
                except (ValueError, TypeError):
                    call_vega = call_delta = call_oi = call_price = 0
                    
                try:
                    put_vega = float(data.get(f"{put_symbol}:VEGA", 0))
                    put_delta = float(data.get(f"{put_symbol}:DELTA", 0))
                    put_oi = float(data.get(f"{put_symbol}:OPEN_INT", 0))
                    put_price = float(data.get(f"{put_symbol}:LAST", 0))
                except (ValueError, TypeError):
                    put_vega = put_delta = put_oi = put_price = 0
                
                # If RTD Greeks are zero, calculate using Black-Scholes
                if call_vega == 0 or call_delta == 0:
                    if self.expiry_date and call_price > 0:
                        call_greeks = self.greeks_calculator.calculate_all_greeks(
                            underlying_price, strike, self.expiry_date, 
                            call_price, is_call=True
                        )
                        call_vega = call_greeks['vega']
                        call_delta = call_greeks['delta']
                        
                if put_vega == 0 or put_delta == 0:
                    if self.expiry_date and put_price > 0:
                        put_greeks = self.greeks_calculator.calculate_all_greeks(
                            underlying_price, strike, self.expiry_date, 
                            put_price, is_call=False
                        )
                        put_vega = put_greeks['vega']
                        put_delta = put_greeks['delta']
                
                # Calculate vanna exposure
                vanna = ((call_oi * call_vega * call_delta) - (put_oi * put_vega * put_delta)) * 100

                if abs(vanna) > 0.01:
                    non_zero_count += 1
                    


            except Exception as e:
                print(f"Error calculating Vanna exposure for strike {strike}: {e}")
                vanna = 0
            
            if vanna > 0:
                pos_vanna_values.append(vanna)
                neg_vanna_values.append(0)
            else:
                pos_vanna_values.append(0)
                neg_vanna_values.append(vanna)
        
        return pos_vanna_values, neg_vanna_values

    def _calculate_charm_exposure_values(self, data, strikes, option_symbols):
        """Calculate charm exposure values for histogram display"""
        pos_charm_values = []
        neg_charm_values = []
        
        try:
            underlying_price = float(data.get(f"{self.symbol}:LAST", 0))
        except (ValueError, TypeError):
            underlying_price = 0
            
        if underlying_price == 0:
            return [], []
        
        non_zero_count = 0
        
        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
                
                # Get RTD values first
                try:
                    call_theta = float(data.get(f"{call_symbol}:THETA", 0))
                    call_delta = float(data.get(f"{call_symbol}:DELTA", 0))
                    call_oi = float(data.get(f"{call_symbol}:OPEN_INT", 0))
                    call_price = float(data.get(f"{call_symbol}:LAST", 0))
                except (ValueError, TypeError):
                    call_theta = call_delta = call_oi = call_price = 0
                    
                try:
                    put_theta = float(data.get(f"{put_symbol}:THETA", 0))
                    put_delta = float(data.get(f"{put_symbol}:DELTA", 0))
                    put_oi = float(data.get(f"{put_symbol}:OPEN_INT", 0))
                    put_price = float(data.get(f"{put_symbol}:LAST", 0))
                except (ValueError, TypeError):
                    put_theta = put_delta = put_oi = put_price = 0
                
                # If RTD Greeks are zero, calculate using Black-Scholes
                if call_theta == 0 or call_delta == 0:
                    if self.expiry_date and call_price > 0:
                        call_greeks = self.greeks_calculator.calculate_all_greeks(
                            underlying_price, strike, self.expiry_date, 
                            call_price, is_call=True
                        )
                        call_theta = call_greeks['theta']
                        call_delta = call_greeks['delta']
                        
                if put_theta == 0 or put_delta == 0:
                    if self.expiry_date and put_price > 0:
                        put_greeks = self.greeks_calculator.calculate_all_greeks(
                            underlying_price, strike, self.expiry_date, 
                            put_price, is_call=False
                        )
                        put_theta = put_greeks['theta']
                        put_delta = put_greeks['delta']
                
                # Calculate charm exposure
                charm = ((call_oi * call_theta * call_delta) - (put_oi * put_theta * put_delta)) * 100

                if abs(charm) > 0.01:
                    non_zero_count += 1
                    


            except Exception as e:
                print(f"Error calculating Charm exposure for strike {strike}: {e}")
                charm = 0
            
            if charm > 0:
                pos_charm_values.append(charm)
                neg_charm_values.append(0)
            else:
                pos_charm_values.append(0)
                neg_charm_values.append(charm)
        
        return pos_charm_values, neg_charm_values



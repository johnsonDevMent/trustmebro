"""
Chart Generator for TRUSTMEBRO
Generates charts with vintage academic styling and watermarks
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os


class ChartGenerator:
    """Generate charts with vintage academic styling"""
    
    # Color palette matching the vintage theme
    COLORS = {
        'primary': '#C85A28',      # Burnt orange
        'secondary': '#8B4513',     # Saddle brown
        'accent': '#D4A84B',        # Gold
        'background': '#F5F0E6',    # Paper cream
        'text': '#3D2914',          # Dark brown
        'grid': '#D4C5B0',          # Light tan
        'watermark': '#E8E0D0',     # Very light tan
    }
    
    BAR_COLORS = ['#C85A28', '#8B4513', '#D4A84B', '#6B4423', '#A0522D']
    PIE_COLORS = ['#C85A28', '#D4A84B', '#8B4513', '#CD853F', '#A0522D']
    
    def __init__(self):
        # Set up matplotlib style
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.facecolor'] = self.COLORS['background']
        plt.rcParams['figure.facecolor'] = self.COLORS['background']
        plt.rcParams['axes.edgecolor'] = self.COLORS['text']
        plt.rcParams['axes.labelcolor'] = self.COLORS['text']
        plt.rcParams['xtick.color'] = self.COLORS['text']
        plt.rcParams['ytick.color'] = self.COLORS['text']
        plt.rcParams['text.color'] = self.COLORS['text']
    
    def _add_watermark(self, ax, fig):
        """Add diagonal watermark"""
        fig.text(0.5, 0.5, 'TRUSTMEBRO - PARODY DATA',
                fontsize=20, color=self.COLORS['grid'],
                ha='center', va='center',
                rotation=35, alpha=0.3,
                transform=fig.transFigure,
                fontweight='bold')
    
    def _add_disclaimer(self, ax):
        """Add disclaimer below chart"""
        pass  # Disclaimer is in the caption
    
    def generate_bar_chart(self, data, filepath):
        """Generate a bar chart"""
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        
        labels = data['labels']
        values = data['data']
        
        x = np.arange(len(labels))
        colors = [self.BAR_COLORS[i % len(self.BAR_COLORS)] for i in range(len(labels))]
        
        bars = ax.bar(x, values, color=colors, edgecolor=self.COLORS['text'], linewidth=1)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(f'{val}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=9, fontweight='bold')
        
        # Add error bars (fictional)
        error = [v * 0.1 for v in values]
        ax.errorbar(x, values, yerr=error, fmt='none', color=self.COLORS['text'], capsize=3)
        
        ax.set_xlabel(data.get('x_label', ''), fontsize=11, fontweight='bold')
        ax.set_ylabel(data.get('y_label', ''), fontsize=11, fontweight='bold')
        ax.set_title(data.get('title', 'Analysis Results'), fontsize=12, fontweight='bold', pad=15)
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha='right')
        
        # Add grid
        ax.yaxis.grid(True, linestyle='--', alpha=0.5, color=self.COLORS['grid'])
        ax.set_axisbelow(True)
        
        # Add watermark
        self._add_watermark(ax, fig)
        
        # Add border
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight', 
                   facecolor=self.COLORS['background'], edgecolor='none')
        plt.close()
    
    def generate_pie_chart(self, data, filepath):
        """Generate a pie chart"""
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        
        labels = data['labels']
        values = data['data']
        colors = [self.PIE_COLORS[i % len(self.PIE_COLORS)] for i in range(len(labels))]
        
        # Create explode effect
        explode = [0.02] * len(labels)
        
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            explode=explode,
            wedgeprops={'edgecolor': self.COLORS['text'], 'linewidth': 1.5},
            textprops={'fontsize': 9}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(data.get('title', 'Distribution Analysis'), 
                    fontsize=12, fontweight='bold', pad=15)
        
        # Add watermark
        self._add_watermark(ax, fig)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight',
                   facecolor=self.COLORS['background'], edgecolor='none')
        plt.close()
    
    def generate_line_chart(self, data, filepath):
        """Generate a line chart"""
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        
        labels = data['labels']
        values = data['data']
        
        x = np.arange(len(labels))
        
        # Plot line with markers
        ax.plot(x, values, color=self.COLORS['primary'], linewidth=2.5,
               marker='o', markersize=8, markerfacecolor=self.COLORS['accent'],
               markeredgecolor=self.COLORS['text'], markeredgewidth=1.5)
        
        # Add confidence band (fictional)
        upper = [v + v * 0.15 for v in values]
        lower = [v - v * 0.15 for v in values]
        ax.fill_between(x, lower, upper, alpha=0.2, color=self.COLORS['primary'])
        
        ax.set_xlabel(data.get('x_label', ''), fontsize=11, fontweight='bold')
        ax.set_ylabel(data.get('y_label', ''), fontsize=11, fontweight='bold')
        ax.set_title(data.get('title', 'Trend Analysis'), fontsize=12, fontweight='bold', pad=15)
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha='right')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.5, color=self.COLORS['grid'])
        ax.set_axisbelow(True)
        
        # Add watermark
        self._add_watermark(ax, fig)
        
        # Add border
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight',
                   facecolor=self.COLORS['background'], edgecolor='none')
        plt.close()
    
    def generate_chart(self, data, filepath):
        """Generate chart based on type"""
        chart_type = data.get('type', 'bar')
        
        if chart_type == 'bar':
            self.generate_bar_chart(data, filepath)
        elif chart_type == 'pie':
            self.generate_pie_chart(data, filepath)
        elif chart_type == 'line':
            self.generate_line_chart(data, filepath)
        else:
            # Default to bar
            self.generate_bar_chart(data, filepath)

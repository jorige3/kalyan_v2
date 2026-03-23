import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fpdf import FPDF, XPos, YPos


class PDFReport(FPDF):
    def __init__(self, fonts_dir: Path):
        super().__init__()
        self.fonts_dir = fonts_dir
        self.add_font("DejaVu", "", str(self.fonts_dir / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(self.fonts_dir / "DejaVuSansCondensed-Bold.ttf"))
        self.set_font("DejaVu", "", 12)

    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, f"Kalyan Market Analysis Report - {datetime.now().strftime('%Y-%m-%d')}", 
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

class ReportGenerator:
    """Generates analytical reports in various formats."""
    
    def __init__(self, reports_dir: str = "reports", fonts_dir: str = "fonts"):
        self.reports_dir = Path(reports_dir)
        self.fonts_dir = Path(fonts_dir)
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_console_report(self, predictions: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Prints a summary to the console."""
        print("\n" + "="*60)
        print(f"📊 KALYAN PREDICTION SUMMARY | {datetime.now().strftime('%d-%b-%Y')}")
        print("="*60)
        print(f"Historical Confidence (Top 5): {metrics.get('hit_rate_top5', 0)*100:.2f}%")
        print(f"Historical Confidence (Top 10): {metrics.get('hit_rate_top10', 0)*100:.2f}%")
        print("-" * 60)
        
        print("\n🏆 TOP 5 JODI PICKS:")
        for i, p in enumerate(predictions[:5], 1):
            print(f"{i}. Jodi: {p['value']} | Score: {p['score']:.4f}")
            
        print("\n✨ NEXT TOP 5 (TOTAL 10):")
        for i, p in enumerate(predictions[5:10], 6):
            print(f"{i}. Jodi: {p['value']} | Score: {p['score']:.4f}")
        print("="*60 + "\n")

    def generate_pdf_report(self, predictions: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Path:
        """Generates a PDF report."""
        pdf_path = self.reports_dir / f"kalyan_analysis_{datetime.now():%Y-%m-%d}.pdf"
        
        pdf = PDFReport(self.fonts_dir)
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Summary Section
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "1. Model Performance Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(0, 8, f"Historical Top 5 Hit Rate: {metrics.get('hit_rate_top5', 0)*100:.2f}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Historical Top 10 Hit Rate: {metrics.get('hit_rate_top10', 0)*100:.2f}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Predictions Table
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "2. Top 10 Analytical Picks", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        widths = [20, 30, 40, 60]
        headers = ["Rank", "Jodi", "Score", "Metrics (R/L/A)"]
        
        pdf.set_font("DejaVu", "B", 10)
        for h, w in zip(headers, widths):
            pdf.cell(w, 8, h, 1, align="C")
        pdf.ln()
        
        pdf.set_font("DejaVu", "", 9)
        for i, p in enumerate(predictions[:10], 1):
            m = p['metrics']
            # Safely extract heat metrics if available (might be nested)
            heat_m = m.get('heat', {}) if isinstance(m.get('heat'), dict) else m
            
            metric_str = f"H:{heat_m.get('recent_freq', 0.0):.2f} | R:{m.get('recency_boost', 0.0):.2f} | D:{m.get('delay_boost', 0.0):.1f}"
            
            pdf.cell(widths[0], 7, str(i), 1, align="C")
            pdf.cell(widths[1], 7, p['value'], 1, align="C")
            pdf.cell(widths[2], 7, f"{p['score']:.4f}", 1, align="C")
            pdf.cell(widths[3], 7, metric_str, 1, align="C")
            pdf.ln()
            
        pdf.output(pdf_path)
        self.logger.info(f"PDF report generated: {pdf_path}")
        return pdf_path

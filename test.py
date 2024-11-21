import win32com.client
import openpyxl
import os
import shutil

def export_excel_to_pdf(excel_file_path, pdf_file_path):
    # Create a temporary copy of the workbook
    temp_workbook_path = os.path.join(os.path.dirname(excel_file_path), f"temp_{os.path.basename(excel_file_path)}")
    shutil.copy2(excel_file_path, temp_workbook_path)
    
    # Open the Excel file
    workbook = openpyxl.load_workbook(temp_workbook_path)
    #Get the first sheet
    sheet = workbook[0]
    
    # Open Excel application
    excel_app = win32com.client.Dispatch("Excel.Application")
    excel_app.Visible = False  # Make Excel application invisible

    # Open the workbook in Excel
    workbook_obj = excel_app.Workbooks.Open(temp_workbook_path)
    # Set print settings
    sheet_obj = workbook_obj.Worksheets(1)
    sheet_obj.PageSetup.Orientation = xlLandscape  # Set orientation to landscape
    #sheet_obj.PageSetup.Zoom = True  # Enable zoom control
    sheet_obj.PageSetup.FitToPagesTall = 1  # Don't fit rows to pages
    sheet_obj.PageSetup.FitToPagesWide = 1  # Fit all columns on one page
    sheet_obj.PageSetup.PrintArea = sheet_obj.UsedRange.Address  # Set print area to used range

    # Adjust scaling and margins
    sheet_obj.PageSetup.Zoom = 70  # Set zoom to 100%
    sheet_obj.PageSetup.TopMargin = excel_app.InchesToPoints(0.25)  # Top margin 0.25 inches
    sheet_obj.PageSetup.BottomMargin = excel_app.InchesToPoints(0.25)  # Bottom margin 0.25 inches
    sheet_obj.PageSetup.LeftMargin = excel_app.InchesToPoints(0.25)  # Left margin 0.25 inches
    sheet_obj.PageSetup.RightMargin = excel_app.InchesToPoints(0.25)  # Right margin 0.25 inches


    # Export to PDF
    pdf_file = pdf_file_path
    sheet_obj.ExportAsFixedFormat(0, pdf_file)

    # Close Excel application
    workbook_obj.Close(SaveChanges=False)
    excel_app.Quit()
    
    os.remove(temp_workbook_path)

# Constants for Excel orientation
xlPortrait = 1
xlLandscape = 2

current_dir = os.getcwd()
excel_file_path = os.path.join(current_dir, 'static','cards','Horizontal Jump Fieldcard.xlsx')
pdf_file_path = os.path.join(current_dir, 'output.pdf')
# Example usage
export_excel_to_pdf(excel_file_path, pdf_file_path)
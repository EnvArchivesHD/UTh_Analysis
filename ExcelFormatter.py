import xlsxwriter
import pandas as pd
import Util
import re
import numpy as np


def format(writer, dfs):
    # remove the index by setting the kwarg 'index' to False
    # df.to_excel(excel_writer=writer, sheet_name='Sheet1', index=False)

    header_format = writer.book.add_format({'bold': True, 'align': 'center', 'border': 0, 'font_name': 'Arial', 'font_size': 11})
    constants_header_format = writer.book.add_format({'bold': True, 'align': 'right', 'left': 1, 'top': 1, 'bottom': 1, 'right': 1, 'bg_color': '#ddb310', 'font_name': 'Arial', 'font_size': 11})
    constants_content_format = writer.book.add_format({'align': 'left', 'right': 1, 'top': 1, 'bottom': 1, 'bg_color': '#DCDCDC', 'font_name': 'Arial', 'font_size': 11})
    bottom_border_format = writer.book.add_format({'bold': True, 'align': 'center', 'bottom': 6, 'font_name': 'Arial', 'font_size': 11})
    bottom_top_border_format = writer.book.add_format({'bold': True, 'align': 'center', 'top': 6, 'bottom': 6, 'font_name': 'Arial', 'font_size': 11})
    standard_format = writer.book.add_format({'bg_color': '#d8e4bc', 'align': 'center', 'font_name': 'Arial', 'font_size': 11})
    normal_format = writer.book.add_format({'align': 'center', 'font_name': 'Arial', 'font_size': 11})
    superscript = writer.book.add_format({'bold': True, 'font_script': 1, 'font_name': 'Arial', 'font_size': 11})
    subscript = writer.book.add_format({'bold': True, 'font_script': 2, 'font_name': 'Arial', 'font_size': 11})
    for sheetname, df in dfs.items():  # loop through `dict` of dataframes
        if sheetname == 'Constants' or sheetname == 'Options':
            df.to_excel(writer, sheet_name=sheetname, index=False, header=False)
            worksheet = writer.sheets[sheetname]

            worksheet.set_column(0, 0, None, constants_header_format)
            worksheet.set_column(1, 1, None, constants_content_format)

            for idx, col in enumerate(df.columns):  # loop through all columns
                series = df[col]
                max_len = max((
                    series.astype(str).str.len().max(),  # len of largest item
                    len(str(series.name))  # len of column name/header
                )) + 1  # adding a little extra space
                worksheet.set_column(idx, idx, max_len)  # set column width
        else:

            df.to_excel(writer, sheet_name=sheetname, index=False)  # send df to writer
            worksheet = writer.sheets[sheetname]  # pull worksheet object

            standard = Util.get_standard_number_from_df(df)

            # Set standard row color
            if standard is not None and ('Lab. #' in df or 'Lab.Nr.' in dfs):
                labnrs = list(df['Lab. #'] if 'Lab. #' in df else df['Lab.Nr.'])
                for i in range(len(labnrs)):
                    if labnrs[i] == standard:
                        worksheet.set_row(i+1, None, standard_format)
                    else:
                        worksheet.set_row(i+1, None, normal_format)

            # Set header formats
            if sheetname in ['Input', 'Results', 'Calc', 'U-Tailing', 'Th-Tailing', 'Extra'] or re.match(r"\d+\D*", sheetname):
                worksheet.set_row(0, None, header_format)
                worksheet.set_row(1, None, bottom_border_format)
            elif sheetname in ['Ratios']:
                worksheet.set_row(0, None, bottom_border_format)

            # Set formats in case there are multiple unit rows (if using CombinedResults functionality)
            if sheetname in ['Input', 'Results', 'Calc']:
                for row in np.where(df['Lab. #'] == '')[0]:
                    if row != 0:
                        worksheet.set_row(row+1, None, bottom_top_border_format)

            for idx, col in enumerate(df.columns):  # loop through all columns

                series = df[col]
                max_len = max((
                    series.astype(str).str.len().max(),  # len of largest item
                    len(str(series.name))  # len of column name/header
                )) + 1  # adding a little extra space
                worksheet.set_column(idx, idx, max_len)  # set column width

                if col != '' and re.match(r"Fehler[0-9]+", str(col)):
                    worksheet.write(0, idx, u'Fehler 2σ')
                else:
                    worksheet.write(0, idx, col)

                if re.match(r"234U[0-9]", str(col)):
                    worksheet.write(0, idx, '234U')
                if re.match(r"238U[0-9]", str(col)):
                    worksheet.write(0, idx, '238U')
                if re.match(r"232Th[0-9]", str(col)):
                    worksheet.write(0, idx, '232Th')
                if re.match(r"230Th[0-9]", str(col)):
                    worksheet.write(0, idx, '230Th')
                if re.match(r"229Th[0-9]", str(col)):
                    worksheet.write(0, idx, '229Th')

                for row, value in enumerate(df[col]):
                    if 'o/oo' in str(value):
                        string_split = str(value).split('o/oo')
                        worksheet.write_rich_string(row+1, idx, string_split[0],
                                                    superscript, 'o',
                                                    '/',
                                                    subscript, 'oo',
                                                    string_split[1])


    '''
    # wrap the text in all cells
    wrap_format = workbook.add_format({'text_wrap': True, 'align': 'center'})
    worksheet.set_column(0, len(df.columns) - 1, cell_format=wrap_format)

    # mimic the default pandas header format for use later
    hdr_fmt = workbook.add_format({
        'bold': True,
        'border': 1,
        'text_wrap': True,
        'align': 'center'
    })

    def update_format(curr_frmt, new_prprty, wrkbk):
        """
        Update a cell's existing format with new properties
        """
        new_frmt = curr_frmt.__dict__.copy()

        for k, v in new_prprty.items():
            new_frmt[k] = v

        new_frmt = {
            k: v
            for k, v in new_frmt.items()
            if (v != 0) and (v is not None) and (v != {}) and (k != 'escapes')
        }

        return wrkbk.add_format(new_frmt)

    # create new border formats
    header_right_thick = update_format(hdr_fmt, {'right': 2}, workbook)
    normal_right_thick = update_format(wrap_format, {'right': 2}, workbook)
    normal_bottom_thick = update_format(wrap_format, {'bottom': 2}, workbook)
    normal_corner_thick = update_format(wrap_format, {
        'right': 2,
        'bottom': 2
    }, workbook)

    # list the 0-based indices where you want bold vertical border lines
    vert_indices = [2, 5, 6]

    # create vertical bold border lines
    for i in vert_indices:
        # header vertical bold line
        worksheet.conditional_format(0, i, 0, i, {
            'type': 'formula',
            'criteria': 'True',
            'format': header_right_thick
        })
        # body vertical bold line
        worksheet.conditional_format(1, i,
                                     len(df.index) - 1, i, {
                                         'type': 'formula',
                                         'criteria': 'True',
                                         'format': normal_right_thick
                                     })
        # bottom corner bold lines
        worksheet.conditional_format(len(df.index), i, len(df.index), i, {
            'type': 'formula',
            'criteria': 'True',
            'format': normal_corner_thick
        })
    # create bottom bold border line
    for i in [i for i in range(len(df.columns) - 1) if i not in vert_indices]:
        worksheet.conditional_format(len(df.index), i, len(df.index), i, {
            'type': 'formula',
            'criteria': 'True',
            'format': normal_bottom_thick
        })'''

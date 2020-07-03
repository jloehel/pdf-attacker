import os
import sys
import time

from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LTFigure, LTText, LTTextBox, LTTextBoxVertical, LTTextBoxHorizontal


def shadow_hide_preventor(document):
    warnings = 0
    file = open(document, 'rb')

    #Create resource manager
    rsrcmgr = PDFResourceManager()
    #Set parameters for analysis.
    laparams = LAParams()
    #Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(file):
        interpreter.process_page(page)  
        #Receive the LTPage object for the page.
        layout = device.get_result()

        #Search for elements in pdf
        for element0 in layout:      
            if isinstance(element0, LTFigure or LTText or LTTextBox or LTTextBoxVertical or LTTextBoxHorizontal):
                s = str(element0)
                tmp = s.split(" ")
                #Extract text name
                figure_name = tmp[0]

                #Extract coordinates (figure)
                coordinates_a = tmp[1].split(",")

                #Set points for rectangle a 
                a_left = float(coordinates_a[0])
                a_bottom = float(coordinates_a[1])
                a_right = float(coordinates_a[2])
                a_top = float(coordinates_a[3])

                #Search for text in pdf
                for element1 in layout:
                    if isinstance(element1, LTText or LTTextBox or LTTextBoxVertical or LTTextBoxHorizontal):
                        s = str(element1)
                        tmp = s.split(" ")
                        #Extract coordinates (text)
                        coordinates_b = tmp[1].split(",")

                        #Extract text from content
                        text_content = s[s.index(coordinates_b[3]) + len(coordinates_b[3]):]

                        #Set points for rectangle b
                        b_left = float(coordinates_b[0])
                        b_bottom = float(coordinates_b[1])
                        b_right = float(coordinates_b[2])
                        b_top = float(coordinates_b[3])

                        #Calculate surface area for rectangle b
                        b_S = (b_right - b_left) * (b_top - b_bottom)

                        #Calculate overlap
                        a_b_I = max(0, min(a_right, b_right) - max(a_left, b_left)) * max(0, min(a_top, b_top) - max(a_bottom, b_bottom))

                        #Caluculate ratio r
                        r = a_b_I / b_S

                        #Calculate overlap in percentage p
                        p = round((r*100), 2)

                        if (p > 0 and p < 100):
                            warnings += 1
                            print('WARNING! element: "' + figure_name + '" overlaps ' + str(p) + ' percent of the following content:\n' + text_content)
                        if (p >= 100):
                            warnings += 1
                            print('WARNING! element: "' + figure_name + '" overlaps completely the following content:\n' + text_content)
    file.close()
    return warnings;

def shadow_hide_and_hide_replace_detector(document):
    warnings = 0

    file = open(document, 'rb')
    content_encoded = file.read()
    file.close()
    content = content_encoded.decode("iso-8859-1")
    content_str = str(content)
    content_str_lower = content_str.lower()
    
    #Get byte value of first signature
    tmp = content_str_lower.find("/type/sig")
    if (tmp > 0):
        index_of_first_sig = tmp
    else:
        index_of_first_sig = content_str_lower.find("/type /sig")

    #Get byte value of EOFs.
    i = 0
    index_of_eof = [content_str.find("%%EOF")+6]    
    if(index_of_eof[0] > 0):
        while(True):
            tmp = content_str.find("%%EOF", index_of_eof[i]+6)
            if(tmp > 0):
                index_of_eof.append(tmp+6)
                i+=1
            else:
                break
    
    if (i == 0):
        print("Error while capturing the EOF byte values!")
        return warnings;

    #Get byte value of signature-EOF 
    index_of_sig_eof = 0
    i = 0
    for byte_value in index_of_eof:
        if (byte_value > index_of_first_sig):
            index_of_sig_eof = index_of_eof[i-1]
            break
        i+=1
    
    #Remove incremental updates
    if(len(content_str) >= index_of_eof[-1]):
        content_str_no_updates = content_str[0: index_of_sig_eof:] + content_str[index_of_eof[-1] + 1::]
    
    
    content_encoded = content_str_no_updates.encode("iso-8859-1")

    tmpfile_str = "tmpfile_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".pdf"
    tmpfile = open(tmpfile_str, "xb")
    tmpfile.write(content_encoded)
    tmpfile.close()


    warnings = compare_files(document, tmpfile_str)
    if os.path.exists(tmpfile_str):
        os.remove(tmpfile_str)

    return warnings;

def compare_files(document0, document1):
    warnings = 0
    file0 = open(document0, 'rb')

    file1 = open(document1, 'rb')

    #Create resource manager
    rsrcmgr0 = PDFResourceManager()
    rsrcmgr1 = PDFResourceManager()
    #Set parameters for analysis.
    laparams0 = LAParams()
    laparams1 = LAParams()
    #Create a PDF page aggregator object.
    device0 = PDFPageAggregator(rsrcmgr0, laparams=laparams0)
    device1 = PDFPageAggregator(rsrcmgr1, laparams=laparams1)
    interpreter0 = PDFPageInterpreter(rsrcmgr0, device0)
    interpreter1 = PDFPageInterpreter(rsrcmgr1, device1)

    for page0 in PDFPage.get_pages(file0):
        interpreter0.process_page(page0)  
        #Receive the LTPage object for the page.
        layout0 = device0.get_result()

        #Search for elements in pdf
        for element0 in layout0:      
            s0 = str(element0)
            check = 0
            #Search for element in pdf
            for page1 in PDFPage.get_pages(file1):
                #Ignore signature fields
                tmp = s0.split(" ")
                if(tmp[0] == "<LTRect"):
                    check = 1
                    break

                interpreter1.process_page(page1)  
                #Receive the LTPage object for the page.
                layout1 = device1.get_result()
                for element1 in layout1:
                    s1 = str(element1)
                    if (s0 == s1):
                        check = 1
            if (check == 0):
                print('WARNING! Object added from document after signing:\n' + s0)
                warnings+=1
    
    for page1 in PDFPage.get_pages(file1):
        interpreter1.process_page(page1)  
        #Receive the LTPage object for the page.
        layout1 = device1.get_result()

        #Search for elements in pdf
        for element1 in layout1:      
            s1 = str(element1)
            check = 0
            #Search for element in pdf
            for page0 in PDFPage.get_pages(file0):
                #Ignore signature fields
                tmp = s1.split(" ")
                if(tmp[1] == "<LTRect"):
                    check = 1
                    break

                interpreter0.process_page(page0)  
                #Receive the LTPage object for the page.
                layout0 = device0.get_result()
                for element0 in layout0:
                    s0 = str(element0)
                    if (s1 == s0):
                        check = 1
            if (check == 0):
                print('WARNING! Object removed from document after signing:\n' + s1)
                warnings+=1



    file0.close()
    file1.close()
    return warnings;

def check_sig_state(document):
    sig_state = 0
    file = open(document, 'rb')
    content = file.read()
    file.close()
    content = content.decode("iso-8859-1")
    content_str = str(content)
    
    #Check if the pdf contains signatures
    sig_state = content_str.count("/Type/Sig")
    if (sig_state <= 0):
        sig_state = content_str.count("/Type /Sig")

    
    return sig_state

#Start
#Check arguments
if(len(sys.argv) < 2):
    print("Please pass the PDF file to be checked as argument!")
elif not(str(sys.argv[1]).endswith('.pdf')):
    print("Please pass only PDF files!")
else:
    document = str(sys.argv[1])
    
    if(check_sig_state(document) > 0):
        #Detector
        print("PDF File contains signatures.")
        print("Start Detection-Mode.")
        #Call detector for category Hide and Replace
        warnings_dec_hide_and_replace = shadow_hide_and_hide_replace_detector(document)
        if (warnings_dec_hide_and_replace == 0):
            print('\nCheck complete: no Shadow Attacks in category "Hide" and/or "Hide and Replace" detected.')
        else:
            print('\nCheck complete: WARNING! ' + str(warnings_dec_hide_and_replace) + ' Shadow Attack(s) in category "Hide" and/or "Hide and Replace" detected.')

    else:
        #Preventor
        print("PDF File contains no signatures.")
        print("Start Prevention-Mode.")
        #Call preventor for category Hide
        warnings_pre_hide = shadow_hide_preventor(document)

        if (warnings_pre_hide == 0):
            print('\nCheck complete: no Shadow Attacks in category "Hide" detected.')
        else:
            print('\nCheck complete: WARNING! ' + str(warnings_pre_hide) + ' Shadow Attack(s) in category "Hide" detected.')







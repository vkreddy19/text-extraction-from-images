from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from .forms import FileFieldForm, UploadFileForm
from django.views.generic.edit import FormView
from .models import Burials
import os
import cv2
from keras.preprocessing import image
import numpy as np
from keras.models import load_model
import pytesseract as pt
from datetime import datetime
from django.views.generic import ListView



form_types = {0: 'b1', 1: 'b2', 2: 'b3_lined', 3: 'b4_no_line', 4: 'b5_hand_written'}


def get_form_type(image_path):
    classification_model = load_model('extract/classification_model.h5')
    test_image = image.load_img(image_path, target_size=(64, 64))
    test_image = image.img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)
    result = classification_model.predict(test_image)
    form_type = form_types[result[0].tolist().index(1.0)]
    print("form_type is", form_type)
    return form_type


def handle_uploaded_file(file):

    image_path = write_content_to_disk(file)
    image_name = file.name
    image_id = get_id_from_filename(image_name)
    form_type = get_form_type(image_path)

    original_image = cv2.imread(image_path)
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    (thresh, bw_image) = cv2.threshold(original_image, 127, 255, cv2.THRESH_BINARY)

    if form_type == 'b2':
        lines_image = draw_lines(bw_image[0:200, ])
        hor_lines, vert_lines = find_lines_position(lines_image)
        print(hor_lines, vert_lines)
        try:
            fields = get_b2_values(bw_image, hor_lines, vert_lines)
        except:
            print("unable to parase as b2 image")
            return
        try:
            Burials.objects.get(id=image_id)
            Burials.objects.filter(id=image_id).update(form_type=form_type, time=datetime.now(), image_name=image_name,
                                                       **fields)
        except Burials.DoesNotExist:
            Burials(id=image_id, form_type=form_type, time=datetime.now(), image_name=image_name, **fields).save()

    elif form_type == 'b3_lined':
        lines_image = draw_lines(bw_image[0:250, ], 5, 10, vertical_required=0)
        hor_lines = get_b3_lines_position(lines_image)
        print(hor_lines)
        if len(hor_lines) < 4:
            print("unable to parse as b3 image")
            # raise  ValueError("As")
            return
        if hor_lines[0] < 20:
            hor_lines = hor_lines[1:]
        fields = get_b3_values(bw_image, hor_lines)
        try:
            Burials.objects.get(id=image_id)
            Burials.objects.filter(id=image_id).update(form_type=form_type, time=datetime.now(), image_name=image_name,
                                                       **fields)
        except Burials.DoesNotExist:
            Burials(id=image_id, form_type=form_type, time=datetime.now(), image_name=image_name, **fields).save()
    elif form_type == 'b4_no_line':
        fields = find_b4_values(bw_image[0:250, ])
        if not fields:
            print("unable to parse as b4_no_line")
            # raise ValueError("b4")
            return
        try:
            Burials.objects.get(id=image_id)
            Burials.objects.filter(id=image_id).update(form_type=form_type, time=datetime.now(), image_name=image_name,
                                                       **fields)
        except Burials.DoesNotExist:
            Burials(id=image_id, form_type=form_type, time=datetime.now(), image_name=image_name, **fields).save()
        # raise ValueError("done")
    else:
        print("unsupported form_type")


def get_b2_values(bw_image, hor_lines, vert_lines):

    grave = np.full(bw_image.shape, 255, dtype=bw_image[0][0].dtype)
    grave[hor_lines[0] + 22: hor_lines[1], vert_lines[2] + 5: vert_lines[3]] = bw_image[hor_lines[0] + 22: hor_lines[1], vert_lines[2] + 5: vert_lines[3]]
    # grave = bw_image[hor_lines[0] + 22: hor_lines[1] - 1, vert_lines[2] + 3: vert_lines[3]]
    name = bw_image[0:hor_lines[0]-1, 0:vert_lines[3]]
    date = bw_image[hor_lines[0] + 22: hor_lines[1], 0: vert_lines[0]-1]
    section = bw_image[hor_lines[0] + 22: hor_lines[1], vert_lines[0] + 10: vert_lines[1]-1]
    lot = bw_image[hor_lines[0] + 22: hor_lines[1], vert_lines[1] + 10: vert_lines[2]-1]


    # cv2.imwrite("name.jpg", name)
    # cv2.imwrite("date.jpg", date)
    # cv2.imwrite("section.jpg", section)
    # cv2.imwrite("lot.jpg", lot)
    # cv2.imwrite("grave.jpg", grave)
    result = {
        "name": pt.image_to_string(name),
        "date": pt.image_to_string(date,  config=r"-c tessedit_char_whitelist=0123456789/,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ --psm 6"),
        "section": pt.image_to_string(section),
        "lot": pt.image_to_string(lot),
        "grave": pt.image_to_string(grave, config=r"-c tessedit_char_whitelist=0123456789 --psm 6"),
    }
    result['name'] = result['name'].split("\n")[-1]
    result['date'] = format_date(result['date'])
    print(result)
    return result


def get_b3_values(bw_image, hor_lines):

    row_len = int(bw_image.shape[1] / 2)

    name = bw_image[0:hor_lines[0], 110:]
    lot = bw_image[hor_lines[0] + 4:hor_lines[1], 90:row_len]
    section = bw_image[hor_lines[0] + 4:hor_lines[1], row_len + 70:]
    grave = bw_image[hor_lines[1] + 4:hor_lines[2], 110:row_len]
    date = bw_image[hor_lines[2] + 4:hor_lines[3], 190:row_len + 10]

    # cv2.imwrite("name.jpg", name)
    # cv2.imwrite("date.jpg", date)
    # cv2.imwrite("section.jpg", section)
    # cv2.imwrite("lot.jpg", lot)
    # cv2.imwrite("grave.jpg", grave)
    result = {
        "name": pt.image_to_string(name),
        "date": pt.image_to_string(date,
                                   config=r"-c tessedit_char_whitelist=0123456789/,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ --psm 6"),
        "section": pt.image_to_string(section),
        "lot": pt.image_to_string(lot),
        "grave": pt.image_to_string(grave, config=r"-c tessedit_char_whitelist=0123456789 --psm 6"),
    }
    result['name'] = result['name'].split("\n")[-1]
    result['date'] = format_date(result['date'])
    return result


def find_b4_values(img):
    gray = cv2.bitwise_not(img)
    bw_image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    cv2.imwrite('line image.jpg', bw_image)
    rows_sum = bw_image.sum(axis=1)

    row_indexes = []
    i = 0
    while i < len(rows_sum):
        if not rows_sum[i]:
            i += 1
            continue
        else:
            start = i
            count = 0
            while i < len(rows_sum) and rows_sum[i]:
                count += 1
                i += 1
            if count > 10:
                row_indexes.append((start, i))
        i += 1
    if len(row_indexes) < 4:
        print(row_indexes)
        return
    else:
        print()

    row_len = int(bw_image.shape[1] / 2)

    name = img[row_indexes[0][0]-10:row_indexes[0][1]+10, ]
    lot = img[row_indexes[1][0]-10: row_indexes[1][1]+10, :row_len-40]
    section = img[row_indexes[1][0]-10:row_indexes[1][1]+10, row_len-40:]
    grave = img[row_indexes[2][0]-10: row_indexes[2][1]+10, :row_len-20]
    date = img[row_indexes[3][0]-10: row_indexes[3][1]+10, ]

    # cv2.imwrite("name.jpg", name)
    # cv2.imwrite("date.jpg", date)
    # cv2.imwrite("section.jpg", section)
    # cv2.imwrite("lot.jpg", lot)
    # cv2.imwrite("grave.jpg", grave)
    try:
        result = {
            "name": pt.image_to_string(name),
            "date": pt.image_to_string(date,
                                       config=r"-c tessedit_char_whitelist=0123456789/,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ --psm 6"),
            "section": pt.image_to_string(section),
            "lot": pt.image_to_string(lot),
            "grave": pt.image_to_string(grave, config=r"-c tessedit_char_whitelist=0123456789 --psm 6"),
        }
        result['section'] = result['section'].split("\n")[-1] if result['section'] else ''
        result['date'] = format_date(result['date'])
    except SystemError as e:
        print(e)
        return
    print(result)
    return result

def upload_file(request):
    if request.method == 'POST':
        print(request.FILES)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/burials')
        else:
            print("asda")
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = 'multiple_upload.html'  # Replace with your template.
    success_url = '...'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('files')
        print(files)
        if form.is_valid():
            for f in files:
                print(f)
                handle_uploaded_file(f)
            return HttpResponseRedirect('/burials')
        else:
            return self.form_invalid(form)


def find_lines_position(array_2d): #b2 #black and white
    array_2d = array_2d / 255
    rows_sum = array_2d.sum(axis=1)
    cols_sum = array_2d.sum(axis=0)

    row_indexes = []
    col_indexes = []
    for i in range(1, len(rows_sum)):
        if rows_sum[i-1] != 0:

            if ((rows_sum[i]-rows_sum[i-1])/rows_sum[i-1]) > 8:
                row_indexes.append(i)

    for i in range(1, len(cols_sum)):
        if cols_sum[i-1] != 0 and ((cols_sum[i]-cols_sum[i-1])/cols_sum[i-1]) > 4:
            # print(i, cols_sum[i-1] , cols_sum[i])
            col_indexes.append(i)
    return row_indexes, col_indexes


def get_b3_lines_position(array_2d):
        array_2d = array_2d / 255
        rows_sum = array_2d.sum(axis=1)
        row_indexes = []
        i = 0
        while i < len(rows_sum):
            if not rows_sum[i]:
                i += 1
                continue
            else:
                row_indexes.append(i)
                while i < len(rows_sum) and rows_sum[i]:
                    i += 1
                i += 1

        return row_indexes


def draw_lines(image_array, row_size=5, col_size=3, horizontal_required=1, vertical_required = 1):

    gray = cv2.bitwise_not(image_array)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

    # Create the images that will use to extract the horizontal and vertical lines
    horizontal = np.copy(bw)
    vertical = np.copy(bw)
    # Specify size on horizontal axis
    cols = horizontal.shape[1]
    horizontal_size = cols // col_size
    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))


    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)


    if not vertical_required:
        temp = np.full(horizontal.shape, 0, dtype=horizontalStructure[0][0].dtype)
        mask = temp == 0
        temp[mask] = horizontal[mask]
        return temp

    rows = vertical.shape[0]
    verticalsize = rows // row_size

    # Create structure element for extracting vertical lines through morphology operations
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))

    # Apply morphology operations
    vertical = cv2.erode(vertical, verticalStructure)
    vertical = cv2.dilate(vertical, verticalStructure)

    mask = vertical == 0
    vertical[mask] = horizontal[mask]
    # cv2.imwrite("t1.jpg", vertical)
    return vertical


def format_date(date):
    date_field = date.split("/")
    if len(date_field[-1]) == 2:
        if len(date_field[-1]) == 2:
            date_field[-1] = "19" + date_field[-1]
    elif len(date_field[-1]) == 4: #YYYY
        if date_field[-1].isdigit():
            if date_field[-1][:2] not in ["19", "20"]: #eg: 9016
                if int(date_field[-1][2:]) > 20:
                    date_field[-1] = "19"+date_field[-1][2:]
                elif date_field[-1].startswith("2"):
                    date_field[-1] = "20"+date_field[-1][2:]
                elif date_field[-1].startswith("1"):
                    date_field[-1] = "19" + date_field[-1][2:]
    print(date, "/".join(date_field))
    return "/".join(date_field)


def burials(request):
    query_results = Burials.objects.all()
    return render(request, 'burials.html', {'query_results': query_results})


def get_id_from_filename(filename):
    try:
        return filename.split("_")[1]
    except IndexError:
        raise ValueError("Unable to get id from the filename.")


def write_content_to_disk(file):
    with open('extract/tmp/' + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return os.path.join('extract/tmp', file.name)


def my_image(request, file):
    print(file)
    image_data = open(os.path.join("extract/tmp/", file), "rb").read()
    return HttpResponse(image_data, content_type="image/jpg")


class BurialsListView(ListView):
    model = Burials
    template_name = 'burials_list_view.html'

import csv

from django.http import HttpResponse



def export_to_csv(request):
    # The only line to customize
    model_class = Burials

    meta = model_class._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in model_class.objects.all():
        row = writer.writerow([getattr(obj, field) for field in field_names])

    return response
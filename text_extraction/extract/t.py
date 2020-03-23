# import cv2
# from keras.preprocessing import image
# from keras.models import load_model
# import numpy as np
# classifier = load_model('/Users/vamshi/Downloads/OCR/new.h5')
# imagePath = "/Users/vamshi/Documents/EAI6020 Final Project/text-extraction-from-images/dataset/all/iCard_022069_1_DALZELL_ROBERT.jpg"
# image_placeholder = cv2.imread(imagePath)
# test_image = image.load_img(imagePath, target_size = (64, 64))
# test_image = image.img_to_array(test_image)
# print(test_image.shape)
# test_image = np.expand_dims(test_image, axis = 0)
# result = classifier.predict(test_image)
# print(result)

def format_date(date):
    date_field = date.split("/")
    print(len(date_field[-1]))
    if len(date_field[-1]) == 2:
        if len(date_field[-1]) == 2:
            date_field[-1] = "19" + date_field[-1]
    elif len(date_field[-1]) == 4: #YYYY
        print("Asd")
        if date_field[-1].isdigit():
            if date_field[-1][:2] not in ["19", "20"]: #eg: 9016
                print("asd")
                if int(date_field[-1][2:]) > 20:
                    date_field[-1] = "19"+date_field[-1][2:]
                elif date_field[-1].startswith("2"):
                    date_field[-1] = "20"+date_field[-1][2:]
                elif date_field[-1].startswith("1"):
                    date_field[-1] = "19" + date_field[-1][2:]
    print(date, "/".join(date_field))
    return "/".join(date_field)

format_date("6/24/2216")
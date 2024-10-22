import pixellib
import os
from pixellib.torchbackend.instance import instanceSegmentation

ins = instanceSegmentation()
## Это нужно скачать отсюда https://github.com/ayoolaolafenwa/PixelLib/blob/master/Tutorials/Pytorch_image_instance_segmentation.md#:~:text=Download%20the%20PointRend%20model.
ins.load_model("/Users/albert.bikeev/Projects/sobaken-id/trained_models/segm_PixelLib_pointrend_resnet50.pkl")
target_classes = ins.select_target_classes(dog=True, sheep=True, bear=True)
# save_extracted_objects=True - сохраняет вырезанные объекты в папках в input_folder почему-то,
# но можно то же самое из res или out вытащить похоже
res, out = ins.segmentBatch(input_folder="data/filtered_dom_lapkin_2_small", segment_target_classes=target_classes,
                            show_bboxes=False, extract_segmented_objects=True,
                            save_extracted_objects=True,
                            output_folder_name="data/filtered_dom_lapkin_2_small_segmented",
                            text_size=1.1)
print('\n\n\n\n\n------------------------------')
print('res:')
print(res)
print('\n\n\n\n\n------------------------------')
print('out:')
print(out)

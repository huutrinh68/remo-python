import time

import remo
from remo.domain.annotation_set import AnnotationSet


def create_dataset_from_local_files(sdk):
    # on Windows path looks like: C:\\Users\\volodymyr\\dataset\\train"
    dataset = sdk.create_dataset('Demo: local files', local_files=['/Users/vovka/Downloads/Datasets/COCO/2014'])
    print('dataset:', dataset)


def create_dataset_from_remote_files(sdk):
    dataset = sdk.create_dataset('Demo', urls=[
        "https://remo-sample-datasets.s3-eu-west-1.amazonaws.com/Imagenet_sample_dataset.zip"],
                                 annotation_task=remo.AnnotationTask.image_classification)
    dataset.browse()
    # wait a bit for uploading and parsing annotations
    time.sleep(5)
    dataset.fetch()
    dataset.annotate()


def export_annotations(sdk):
    annotation_set = AnnotationSet(sdk, id=6)
    print(annotation_set.export_annotations())


def list_all_datasets():
    print(remo.datasets())


def list_all_annotation_sets():
    for dataset in remo.datasets():
        print(dataset)
        for annotation_set in dataset.annotation_sets():
            print('>>>', annotation_set)


if __name__ == '__main__':
    list_all_annotation_sets()

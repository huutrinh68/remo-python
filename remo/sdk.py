from .api import API
from .ui import UI
from .domain.interfaces import ISDK
from .domain.dataset import Dataset
from .domain.annotation_set import AnnotationSet
from .domain.task import AnnotationTask
from .utils import browse


class SDK(ISDK):
    def __init__(self, API, UI):
        self.api = API
        self.ui = UI


    def create_dataset(self, name, local_files=[], paths_to_upload=[], urls=[], annotation_task=None,
                          public=False):

            ''' 
            Creates a new dataset in Remo and optionally populate it with images and annotation from local drive or URL

            Args:
               name: string, name of the Dataset

               local_files: list of files or directories. Function will scan for .png, .jpeg, .tiff and .jpg in the folders and sub-folders.

               paths_to_upload: list of files or directories. These files will be uploaded to the local disk.
                  - files supported: image files, annotation files and archive files.
                  - Annotation files: json, xml, csv. If annotation file is provided, you need to provide annotation task.
                  - Archive files: zip, tar, gzip. These files are unzipped, and then we scan for images, annotations and other archives. Support for nested archive files, image and annotation files in the same format supported elsewhere

               urls: list of urls pointing to downloadable target, which should be an archive file. The function will download the target of the URL, scan for archive files, unpack them and the results will be scanned for images, annotations and other archives.

               annotation_task:
                   object_detection = 'Object detection'. Supports Coco, Open Images, Pascal
                   instance_segmentation = 'Instance segmentation'. Supports Coco
                   image_classification = 'Image classification'. ImageNet

              public: do not use it for now :)

            Returns: remo Dataset
            '''

            result = self.api.create_dataset(name, public)
            print(result)
            my_dataset = Dataset(self, **result)
            my_dataset.add_data(local_files, paths_to_upload, urls, annotation_task)
            my_dataset.initialise_images()

            return my_dataset

    def list_datasets(self) -> [Dataset]:
        resp = self.api.list_datasets()
        return [
            Dataset(self, id=dataset['id'], name=dataset['name'])
            for dataset in resp.get('results', [])
        ]

    def get_dataset(self, dataset_id) -> Dataset:
        result = self.api.get_dataset(dataset_id)
        return Dataset(self, **result)

     # MC: Can annotation_task have a default value?
    def add_data_to_dataset(self, dataset_id, local_files=[],
                            paths_to_upload=[], urls=[], annotation_task=None, folder_id=None):
        '''

            
        Adds data to existing dataset
        
        Args:
            dataset_id: id of the desired dataset to extend (integer)
            local_files: list of files or directories. Function will scan for .png, .jpeg, .tiff and .jpg in the folders and sub-folders.
            paths_to_upload: list of files or directories. These files will be uploaded to the local disk.

               files supported: image files, annotation files and archive files.

               Annotation files: json, xml, csv. If annotation file is provided, you need to provide annotation task.

               Archive files: zip, tar, gzip. These files are unzipped, and then we scan for images, annotations and other archives. Support for nested archive files, image and annotation files in the same format supported elsewhere

            urls: list of urls pointing to downloadable target, which should be an archive file. The function will download the target of the URL - then we scan for archive files, unpack them and proceed as per Archive file section.

            annotation_task:
               object_detection = 'Object detection'. Supports Coco, Open Images, Pascal
               instance_segmentation = 'Instance segmentation'. Supports Coco
               image_classification = 'Image classification'. ImageNet
            folder_id: if there is a folder in the targer remo id, and you want to add images to a specific folder, you can specify it here.
        '''

        result = {}
        if len(local_files):
            if type(local_files) is not list:
                raise ValueError(
                    'Function parameter "paths_to_add" should be a list of file or directory paths, but instead is a ' + str(
                        type(local_files)))

            files_upload_result = self.api.upload_local_files(dataset_id, local_files, annotation_task, folder_id)
            result['files_link_result'] = files_upload_result

        if len(paths_to_upload):
            if type(paths_to_upload) is not list:
                raise ValueError(
                    'Function parameter "paths_to_upload" should be a list of file or directory paths, but instead is a ' + str(
                        type(paths_to_upload)))

            files_upload_result = self.api.bulk_upload_files(dataset_id=dataset_id,
                                                             files_to_upload=paths_to_upload,
                                                             annotation_task=annotation_task, 
                                                             folder_id=folder_id)

            result['files_upload_result'] = files_upload_result

        if len(urls):
            if type(urls) is not list:
                raise ValueError(
                    'Function parameter "urls" should be a list of URLs, but instead is a ' + str(type(urls)))

            urls_upload_result = self.api.upload_urls(dataset_id=dataset_id,
                                                      urls=urls,
                                                      annotation_task=annotation_task,
                                                      folder_id=folder_id)

            print(urls_upload_result)
            result['urls_upload_result'] = urls_upload_result
        return result

    def list_annotation_sets(self, dataset_id):
        resp = self.api.list_annotation_sets(dataset_id)
        return [
            AnnotationSet(self,
                          id=annotation_set['id'],
                          name=annotation_set['name'],
                          task=AnnotationTask(annotation_set['task']['name']),
                          total_classes=annotation_set['statistics']['total_classes'])
            for annotation_set in resp.get('results', [])
        ]
    
    def annotation_statistics(self, dataset_id):
        resp = self.api.list_annotation_sets(dataset_id)
        return [
            "Annotation set {id} - '{name}',  #images: {total_images}, #classes: {total_classes}, #objects: {total_annotation_objects}, Top3 classes: {top3_classes}, Released: {released_at}, Updated: {updated_at} ".format(
                id=annotation_set['id'], name=annotation_set['name'],
                total_images=annotation_set['total_images'], 
                total_classes=annotation_set['statistics']['total_classes'],
                total_annotation_objects=annotation_set['statistics']['total_annotation_objects'],   
                top3_classes=[(i['name'], i['count']) for i in annotation_set['statistics']['top3_classes']],
                released_at=annotation_set.get('released_at'),
                updated_at=annotation_set['updated_at'])
            for annotation_set in resp.get('results', [])
        ]
   
      
    
    
    def list_dataset_images(self, dataset_id, folder_id=None, endpoint=None, **kwargs):
        
        if folder_id is not None:
            result = self.api.list_dataset_contents_by_folder(dataset_id, folder_id, **kwargs)
        else:
            result = self.api.list_dataset_contents(dataset_id, **kwargs)
        images = []
        
        for entry in result.get('results', []):
            my_dict = {}
            my_dict['name'] = entry.get('name')
            my_dict['id'] = entry.get('id')
            images.append(my_dict)
            
        return images

    def get_annotations(self, annotation_set_id: int, annotation_format='json'):
        """
        Args:
            annotation_format: choose format from this list ['json', 'coco'], default = 'json'
        Returns: annotations, format: list of dicts
        """
        return self.api.get_annotations(annotation_set_id, annotation_format)
    
    def export_annotation_json_to_csv(self, annotation, output_file='output.csv', task=None):
        return self.api.export_annotation_json_to_csv(annotation, output_file, task)
    
    def view_image(self, image_id, dataset_id):
        """
        Opens browser on the image view for giving image
        """
        img_list = self.list_dataset_images(dataset_id)
        contain = False
        for img_dict in img_list:
            if image_id == img_dict['id']:
                contain = True
                browse(self.ui.image_view(image_id, dataset_id))
        if not contain:
            msg = 'Image ID: %s' % str(image_id) + ' not in dataset %s' % str(dataset_id)
            print(msg)
                

    def view_search(self, cls=None, task=None):
        """
        Opens browser in search page
        """
        browse(self.ui.search_url())

    def get_images(self, dataset_id, image_id):
        return self.api.get_images(dataset_id, image_id)
    
    def search_class(self, class_name):
        return self.api.search_class(class_name)


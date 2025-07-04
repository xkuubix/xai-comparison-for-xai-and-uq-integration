from torch.utils.data import Dataset
import os
import pandas as pd
from PIL import Image
from pydicom import dcmread
import numpy as np
import torch
import torchvision.transforms.functional as TF
from torchvision import transforms as T
import logging
logger = logging.getLogger(__name__)

class TompeiDataset(Dataset):
    def __init__(self, df, transform=None, config=None):
        """
        Args:
            df (pd.DataFrame): DataFrame containing image metadata.
            image_dir (str): Directory where images are stored.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.df = df
        self.class_name = df['ClassificationMapped']
        self.transform = transform
        logger.info(f"Dataset initialized with {len(self.df)} samples.")
        self.config = config

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        img_name = os.path.join(self.df.iloc[idx]['ImagePath'])
        image = dcmread(img_name).pixel_array
        if image.ndim == 2:  # If grayscale, convert to RGB
            image = np.stack((image,)*3, axis=-1)
        mask_name = os.path.join(self.df.iloc[idx]['MaskPath'])
        mask = Image.open(mask_name)
        label_str = self.df.iloc[idx]['ClassificationMapped']
        if self.config:
            if self.config['training_plan']['criterion'].lower() == 'bce':
                label = 0. if label_str == 'Negative' else 1.
                label = torch.tensor(label, dtype=torch.float32)
            elif self.config['training_plan']['criterion'].lower() == 'ce':
                label = 0 if label_str == 'Negative' else 1
                label = torch.tensor(label, dtype=torch.long)

        metadata = self.df.iloc[idx].to_dict()

        if self.transform:
            # TODO add albumentation transformations
            image = self.transform(image)
            pass

        if self.df.iloc[idx]['LeftRight'] == 'R':
            image = T.RandomHorizontalFlip(p=1.0)(image)
            mask = TF.hflip(mask)

        mask = np.array(mask, dtype=np.bool)
        return {"image": image,
                "target": {
                    "mask": mask,
                    "label": label,
                },
                "metadata": metadata}
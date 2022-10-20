from torch.utils.data import Dataset
import numpy as np


class BaseDataset(Dataset):
    """
    Define length and sampling method
    """
    def __init__(self, root_dir, split='train', downsample=1.0):
        self.root_dir = root_dir
        self.split = split
        self.downsample = downsample
        self.random_rays = False

    def read_intrinsics(self):
        raise NotImplementedError

    def __len__(self):
        if self.split.startswith('train'):
            return 1000
        return len(self.poses)

    def __getitem__(self, idx):
        if self.split.startswith('train'):
            # training pose is retrieved in train.py
            if self.ray_sampling_strategy == 'all_images': # randomly select images
                img_idxs = np.random.choice(len(self.poses), self.batch_size)
            elif self.ray_sampling_strategy == 'same_image': # randomly select ONE image
                img_idxs = np.random.choice(len(self.poses), 1)[0]

            if self.random_rays:
                # randomly select pixels
                pix_idxs = np.random.choice(self.img_wh[0]*self.img_wh[1], self.batch_size)
                rays = self.rays[img_idxs, pix_idxs]
            else:
                # select a patch from one image
                patch_start_x = np.random.randint(low=0,
                                                  high=(self.img_wh[0] - self.patch_size * self.patch_sampling_size))
                patch_end_x = patch_start_x + self.patch_size * self.patch_sampling_size
                patch_start_y = np.random.randint(low=0,
                                                  high=(self.img_wh[1] - self.patch_size * self.patch_sampling_size))
                patch_end_y = patch_start_y + self.patch_size * self.patch_sampling_size

                pix_idxs = np.arange(0, self.img_wh[0] * self.img_wh[1]).reshape(self.img_wh[0], self.img_wh[1])[
                           patch_start_x:patch_end_x:self.patch_sampling_size,
                           patch_start_y:patch_end_y:self.patch_sampling_size].flatten()
                img_idxs = np.random.choice(len(self.poses), 1)[0]
                rays = self.rays[img_idxs, pix_idxs]

            sample = {'img_idxs': img_idxs, 'pix_idxs': pix_idxs,
                      'rgb': rays[:, :3]}
            if self.rays.shape[-1] == 4: # HDR-NeRF data
                sample['exposure'] = rays[:, 3:]
        else:
            sample = {'pose': self.poses[idx], 'img_idxs': idx}
            if len(self.rays)>0: # if ground truth available
                rays = self.rays[idx]
                sample['rgb'] = rays[:, :3]
                if rays.shape[1] == 4: # HDR-NeRF data
                    sample['exposure'] = rays[0, 3] # same exposure for all rays

        return sample
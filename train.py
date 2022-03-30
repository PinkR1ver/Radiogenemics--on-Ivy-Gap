import os
from torch import nn, optim
import torch
from torch.utils.data import DataLoader
import torchvision
from data import *
from unet import *
import numpy as np
import traceback
import trainHelper
import sys
from tqdm import tqdm

MRI_series_this = sys.argv[1]
epoches = int(sys.argv[2])

base_path = os.path.dirname(__file__)
data_path = os.path.join(base_path, 'data')
model_path = os.path.join(base_path, 'model', MRI_series_this)
weight_path = os.path.join(model_path, f'{MRI_series_this}_unet.pth')
train_path = os.path.join(data_path, 'train_result')
test_path = os.path.join(data_path, 'test_result')
validation_path = os.path.join(data_path, 'validation_result')

if not os.path.isdir(model_path):
    os.mkdir(model_path)

if not os.path.isdir(os.path.join(train_path, MRI_series_this)):
    os.mkdir(os.path.join(train_path, MRI_series_this))

if not os.path.isdir(os.path.join(validation_path, MRI_series_this)):
    os.mkdir(os.path.join(train_path, MRI_series_this))

if not os.path.isdir(os.path.join(test_path, MRI_series_this)):
    os.mkdir(os.path.join(train_path, MRI_series_this))


if torch.cuda.is_available():
    device = 'cuda'
    print("Using cuda")
else:
    device = 'cpu'
    print("Using CPU")


if __name__ == '__main__':

    GBM_Dataset = ImageDataset(data_path, 'GBM_MRI_Dataset.csv', MRI_series=MRI_series_this, mode='train', resize=(255, 255))

    training_data_size = 0.8

    train_size = int(training_data_size * len(GBM_Dataset))
    validation_size = len(GBM_Dataset) - train_size

    train_dataset, validation_dataset = torch.utils.data.random_split(GBM_Dataset, [train_size, validation_size])

    test_dataset = ImageDataset(data_path, 'GBM_MRI_Dataset.csv', MRI_series=MRI_series_this, mode='test', resize=(255, 255))

    batch_size = 4

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    validation_loader = DataLoader(validation_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    net = UNet().to(device)

    if os.path.exists(weight_path):
        net.load_state_dict(torch.load(weight_path))
        print("Loading Weight Successful")
    else:
        print("Loading Weight Failed")

    opt = optim.Adam(net.parameters())  # stochastic gradient descent
    loss_function = nn.BCELoss()

    f = open(os.path.join(model_path, f'{MRI_series_this}_epoch.txt'), "r")
    epoch = int(f.read())
    f.close()

    evalution_list_train = trainHelper.trainHelper(MRI_series_this=MRI_series_this, mode='train', begin=epoch)
    evalution_list_valitaion = trainHelper.trainHelper(MRI_series_this=MRI_series_this, mode='validation', begin=epoch)
    evalution_list_test =  trainHelper.trainHelper(MRI_series_this=MRI_series_this, mode='test', begin=epoch)

    try:
        for iter_out in tqdm(range(1, epoches + 1)):
            for i, (image, mask) in enumerate(train_loader):
                image, mask = image.to(device), mask.to(device)

                predict_image = net(image)
                train_loss = loss_function(predict_image, mask)

                opt.zero_grad()
                train_loss.backward()
                opt.step()

                evalution_list_train.list_pushback(predict_image, mask, train_loss.item())

                mask[mask >= 0.5] = 1
                mask[mask < 0.5] = 0

                _image = image[0]
                if MRI_series_this == 'Stack':
                    _mask = gray2RGB(mask[0])
                    _pred_Image = gray2RGB(predict_image[0])
                else:
                    _mask = mask[0]
                    _pred_Image = predict_image[0]

                visual_image = torch.stack([_image, _mask, _pred_Image], dim=0)
                torchvision.utils.save_image(visual_image, os.path.join(train_path, MRI_series_this, f'{i}.png'))

            evalution_list_train.list_plot(epoch) 
            evalution_list_train.list_write_into_log(epoch)
            evalution_list_train.average_list_pushback()
            evalution_list_train.clear_list()

            for i, (image, mask) in enumerate(validation_loader):
                image, mask = image.to(device), mask.to(device)

                predict_image = net(image)
                train_loss = loss_function(predict_image, mask)

                opt.zero_grad()
                train_loss.backward()
                opt.step()

                evalution_list_valitaion.list_pushback(predict_image, mask, train_loss.item())

                mask[mask >= 0.5] = 1
                mask[mask < 0.5] = 0

                _image = image[0]
                if MRI_series_this == 'Stack':
                    _mask = gray2RGB(mask[0])
                    _pred_Image = gray2RGB(predict_image[0])
                else:
                    _mask = mask[0]
                    _pred_Image = predict_image[0]

                visual_image = torch.stack([_image, _mask, _pred_Image], dim=0)
                torchvision.utils.save_image(visual_image, os.path.join(validation_path, MRI_series_this, f'{i}.png'))

            evalution_list_valitaion.list_plot(epoch) 
            evalution_list_valitaion.list_write_into_log(epoch)
            evalution_list_valitaion.average_list_pushback()
            evalution_list_valitaion.clear_list()


            for i, (image, mask) in enumerate(test_loader):
                image, mask = image.to(device), mask.to(device)

                predict_image = net(image)
                train_loss = loss_function(predict_image, mask)

                opt.zero_grad()
                train_loss.backward()
                opt.step()

                evalution_list_test.list_pushback(predict_image, mask, train_loss.item())

                mask[mask >= 0.5] = 1
                mask[mask < 0.5] = 0

                _image = image[0]
                if MRI_series_this == 'Stack':
                    _mask = gray2RGB(mask[0])
                    _pred_Image = gray2RGB(predict_image[0])
                else:
                    _mask = mask[0]
                    _pred_Image = predict_image[0]

                visual_image = torch.stack([_image, _mask, _pred_Image], dim=0)
                torchvision.utils.save_image(visual_image, os.path.join(validation_path, MRI_series_this, f'{i}.png'))

            evalution_list_test.list_plot(epoch) 
            evalution_list_test.list_write_into_log(epoch)
            evalution_list_test.average_list_pushback()
            evalution_list_test.clear_list()

        evalution_list_train.average_list_plot(epoch)
        evalution_list_train.average_list_write_into_log(epoch)

        evalution_list_valitaion.average_list_plot(epoch)
        evalution_list_valitaion.average_list_write_into_log(epoch)

        evalution_list_test.average_list_plot(epoch)
        evalution_list_test.average_list_write_into_log(epoch)

    except:
        print('Exception!!!')
        if not os.path.isfile(os.path.join(base_path, 'exception_in_trainning', f'{MRI_series_this}_log.txt')):
            f = open(os.path.join(base_path, 'exception_in_trainning', f'{MRI_series_this}_log.txt'), 'x')
            f.close()
        f = open(os.path.join(base_path, 'exception_in_trainning',
                 f'{MRI_series_this}_log.txt'), 'a')
        f.write(f'exception in epoch{epoch}\n')
        f.write(traceback.format_exc())
        f.write('\n')
        f.close()

        if evalution_list_train.loss_average_list.size !=0:
            evalution_list_train.average_list_plot(epoch)
            evalution_list_train.average_list_write_into_log(epoch)

            evalution_list_valitaion.average_list_plot(epoch)
            evalution_list_valitaion.average_list_write_into_log(epoch)

            evalution_list_test.average_list_plot(epoch)
            evalution_list_test.average_list_write_into_log(epoch)

        trainHelper.sendmail(content=r'Your train.py went something wrong', subject=r'train.py go wrong')
    
    else:
        print("Train finishing")
        if evalution_list_train.loss_average_list.size !=0:
            evalution_list_train.average_list_plot(epoch)
            evalution_list_train.average_list_write_into_log(epoch)

            evalution_list_valitaion.average_list_plot(epoch)
            evalution_list_valitaion.average_list_write_into_log(epoch)

            evalution_list_test.average_list_plot(epoch)
            evalution_list_test.average_list_write_into_log(epoch)

        trainHelper.sendmail(content=r'Your train.py run success', subject=r'train.py finished')

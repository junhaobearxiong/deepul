import numpy as np
import torch.nn as nn
import torch.utils.data
import torchvision
from torchvision import transforms as transforms
from .utils import *
from .hw3_utils.hw3_models import GoogLeNet
from PIL import Image as PILImage
import scipy.ndimage
import cv2
import deepul.pytorch_util as ptu

import numpy as np
import math
import sys

softmax = None
model = None
device = torch.device("cuda:0")

def plot_gan_training(losses, title, fname):
    plt.figure()
    n_itr = len(losses)
    xs = np.arange(n_itr)

    plt.plot(xs, losses, label='loss')
    plt.legend()
    plt.title(title)
    plt.xlabel('Training Iteration')
    plt.ylabel('Loss')
    savefig(fname)

def q1_gan_plot(data, samples, xs, ys, title, fname):
    plt.figure()
    plt.hist(samples, bins=50, density=True, alpha=0.7, label='fake')
    plt.hist(data, bins=50, density=True, alpha=0.7, label='real')

    plt.plot(xs, ys, label='discrim')
    plt.legend()
    plt.title(title)
    savefig(fname)


######################
##### Question 1 #####
######################

def q1_data(n=20000):
    assert n % 2 == 0
    gaussian1 = np.random.normal(loc=-1.5, scale=0.35, size=(n//2,))
    gaussian2 = np.random.normal(loc=0.2, scale=0.6, size=(n//2,))
    data = (np.concatenate([gaussian1, gaussian2]) + 1).reshape([-1, 1])
    scaled_data = (data - np.min(data)) / (np.max(data) - np.min(data) + 1e-8)
    return 2 * scaled_data -1

def visualize_q1_dataset():
    data = q1_data()
    plt.hist(data, bins=50, alpha=0.7, label='train data')
    plt.legend()
    plt.show()


def q1_save_results(part, fn):
    data = q1_data()
    losses, samples1, xs1, ys1, samples_end, xs_end, ys_end = fn(data)

    # loss plot
    plot_gan_training(losses, 'Q1{} Losses'.format(part), 'results/q1{}_losses.png'.format(part))

    # samples
    q1_gan_plot(data, samples1, xs1, ys1, 'Q1{} Epoch 1'.format(part), 'results/q1{}_epoch1.png'.format(part))
    q1_gan_plot(data, samples_end, xs_end, ys_end, 'Q1{} Final'.format(part), 'results/q1{}_final.png'.format(part))

######################
##### Question 2 #####
######################

def calculate_is(samples):
    assert (type(samples[0]) == np.ndarray)
    assert (len(samples[0].shape) == 3)

    model = GoogLeNet().to(ptu.device)
    model.load_state_dict(torch.load("../../deepul/hw3_utils/classifier.pt"))
    softmax = nn.Sequential(model, nn.Softmax(dim=1))

    bs = 100
    softmax.eval()
    with torch.no_grad():
        preds = []
        n_batches = int(math.ceil(float(len(samples)) / float(bs)))
        for i in range(n_batches):
            sys.stdout.write(".")
            sys.stdout.flush()
            inp = ptu.FloatTensor(samples[(i * bs):min((i + 1) * bs, len(samples))])
            pred = ptu.get_numpy(softmax(inp))
            preds.append(pred)
    preds = np.concatenate(preds, 0)
    kl = preds * (np.log(preds) - np.log(np.expand_dims(np.mean(preds, 0), 0)))
    kl = np.mean(np.sum(kl, 1))
    return np.exp(kl)

def load_q2_data():
    train_data = torchvision.datasets.CIFAR10("./data", transform=torchvision.transforms.ToTensor(),
                                              download=True, train=True)
    return train_data

def visualize_q2_data():
    train_data = load_q2_data()
    imgs = train_data.data[:100]
    show_samples(imgs, title=f'CIFAR-10 Samples')

def q2_save_results(fn):
    train_data = load_q2_data()
    train_data = train_data.data.transpose((0, 3, 1, 2)) / 255.0
    train_losses, samples = fn(train_data)

    print("Inception score:", calculate_is(samples.transpose([0, 3, 1, 2])))
    plot_gan_training(train_losses, 'Q2 Losses', 'results/q2_losses.png')
    show_samples(samples[:100] * 255.0, fname='results/q2_samples.png', title=f'CIFAR-10 generated samples')

######################
##### Question 3 #####
######################

def load_q3_data():
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    train_data = torchvision.datasets.CIFAR10(root="./data", train=True, download=True, transform=transform).data.transpose((0, 3, 1, 2)) / 255.0
    test_data = torchvision.datasets.CIFAR10(root="./data", train=False, download=True, transform=transform).data.transpose((0, 3, 1, 2)) / 255.0
    return train_data, test_data


def visualize_q3_data():
    train_data, _ = load_q3_data()
    imgs = train_data.data[:100]
    show_samples(imgs.reshape([100, 28, 28, 1]) * 255.0, title='CIFAR10 samples')

def save_plot(
    train_losses: np.ndarray, test_losses: np.ndarray, title: str, fname: str
) -> None:
    plt.figure()
    if test_losses is None:
        plt.plot(train_losses, label="train")
        plt.xlabel("Iteration")
    else:
        n_epochs = len(test_losses) - 1
        x_train = np.linspace(0, n_epochs, len(train_losses))
        x_test = np.arange(n_epochs + 1)

        plt.plot(x_train, train_losses, label="train")
        plt.plot(x_test, test_losses, label="test")
        plt.xlabel("Epoch")
    plt.legend()
    plt.title(title)
    plt.ylabel("loss")
    savefig(fname)


def q3_save_results(fn, part):
    train_data, test_data = load_q3_data()
    gan_losses, lpips_losses, l2_train_losses, l2_val_losses, recon_show = fn(train_data, test_data, test_data[:100])

    plot_gan_training(gan_losses, f'Q3{part} Discriminator Losses', f'results/q3{part}_gan_losses.png')
    save_plot(l2_train_losses, l2_val_losses, f'Q3{part} L2 Losses', f'results/q3{part}_l2_losses.png')
    save_plot(lpips_losses, None, f'Q3{part} LPIPS Losses', f'results/q3{part}_lpips_losses.png')
    show_samples(test_data[:100].transpose(0, 2, 3, 1) * 255.0, nrow=20, fname=f'results/q3{part}_data_samples.png', title=f'Q3{part} CIFAR10 val samples')
    show_samples(recon_show * 255.0, nrow=20, fname=f'results/q3{part}_reconstructions.png', title=f'Q3{part} VQGAN reconstructions')
    print('final_val_reconstruction_loss:', l2_val_losses[-1])

######################
##### Question 4 #####
######################

def get_colored_mnist(data):
    # from https://www.wouterbulten.nl/blog/tech/getting-started-with-gans-2-colorful-mnist/
    # Read Lena image
    lena = PILImage.open('deepul/deepul/hw3_utils/lena.jpg')

    # Resize
    batch_resized = np.asarray([scipy.ndimage.zoom(image, (2.3, 2.3, 1), order=1) for image in data])

    # Extend to RGB
    batch_rgb = np.concatenate([batch_resized, batch_resized, batch_resized], axis=3)

    # Make binary
    batch_binary = (batch_rgb > 0.5)

    batch = np.zeros((data.shape[0], 28, 28, 3))

    for i in range(data.shape[0]):
        # Take a random crop of the Lena image (background)
        x_c = np.random.randint(0, lena.size[0] - 64)
        y_c = np.random.randint(0, lena.size[1] - 64)
        image = lena.crop((x_c, y_c, x_c + 64, y_c + 64))
        image = np.asarray(image) / 255.0

        # Invert the colors at the location of the number
        image[batch_binary[i]] = 1 - image[batch_binary[i]]

        batch[i] = cv2.resize(image, (0, 0), fx=28 / 64, fy=28 / 64, interpolation=cv2.INTER_AREA)
    return batch.transpose(0, 3, 1, 2)

def _load_q4_data():
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    train_data = torchvision.datasets.MNIST(root="./data", train=True, download=True, transform=transform)
    test_data = torchvision.datasets.MNIST(root="./data", train=False, download=True, transform=transform)
    return train_data, test_data

def load_q4_data():
    train, _ = _load_q4_data()
    mnist = np.array(train.data.reshape(-1, 28, 28, 1) / 255.0)
    colored_mnist = get_colored_mnist(mnist)
    return mnist.transpose(0, 3, 1, 2), colored_mnist

def visualize_cyclegan_datasets():
    mnist, colored_mnist = load_q4_data()
    mnist, colored_mnist = mnist[:100], colored_mnist[:100]
    show_samples(mnist.reshape([100, 28, 28, 1]) * 255.0, title=f'MNIST samples')
    show_samples(colored_mnist.transpose([0, 2, 3, 1]) * 255.0, title=f'Colored MNIST samples')

def q4_save_results(fn):
    mnist, cmnist = load_q4_data()

    m1, c1, m2, c2, m3, c3 = fn(mnist, cmnist)
    m1, m2, m3 = m1.repeat(3, axis=3), m2.repeat(3, axis=3), m3.repeat(3, axis=3)
    mnist_reconstructions = np.concatenate([m1, c1, m2], axis=0)
    colored_mnist_reconstructions = np.concatenate([c2, m3, c3], axis=0)

    show_samples(mnist_reconstructions * 255.0, nrow=20,
                 fname='figures/q4_mnist.png',
                 title=f'Source domain: MNIST')
    show_samples(colored_mnist_reconstructions * 255.0, nrow=20,
                 fname='figures/q4_colored_mnist.png',
                 title=f'Source domain: Colored MNIST')

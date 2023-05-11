import torch
import gpytorch
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from deepkl.models import SpectralMixtureGPModel
from deepkl.trainers import SpectralMixtureTrainer
from sklearn.preprocessing import MinMaxScaler

plt.style.use('seaborn-whitegrid')
matplotlib.use('Agg')

def prepare_data():
    
    flx = pd.read_csv('data/FLX_FI-Hyy_FLUXNET2015_FULLSET_HH_1996-2014_1-4_saba.csv').loc[11000:11916]
    train_x = flx['TA_F'].loc[11000:11744].index.values
    train_y = flx['NEE_VUT_50'].loc[11000:11744].values

    validate_x = flx['TA_F'].loc[11745:11900].index.values
    validate_y = flx['NEE_VUT_50'].loc[11745:11900].values

    
    # minmax scale the data
    mm = MinMaxScaler()
    train_y = mm.fit_transform(train_y.reshape(-1,1)).ravel()
    validate_y = mm.transform(validate_y.reshape(-1,1)).ravel()

    train_x = torch.stack([torch.from_numpy(np.array(i)) for i in train_x]).double()
    train_y = torch.stack([torch.from_numpy(np.array(i)) for i in train_y]).double()

    validate_x = torch.stack([torch.from_numpy(np.array(i)) for i in validate_x]).double()
    validate_y = torch.stack([torch.from_numpy(np.array(i)) for i in validate_y]).double()
    return (train_x, train_y), (validate_x, validate_y)

def test_spectral_mixture():
    """
    Spectral Mixture GP 
    """
    (train_x, train_y), (validate_x, validate_y) = prepare_data()
    
    likelihood = gpytorch.likelihoods.GaussianLikelihood()
    model = SpectralMixtureGPModel(train_x, train_y, num_mixtures=2, likelihood=likelihood)
    
    trainer = SpectralMixtureTrainer(model, likelihood, lr=0.15)
    trainer.train_batch(train_x, train_y, epochs=220)
    
    posterior_model, posterior_likelihood = trainer.model, trainer.likelihood
    
    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        
        domain = torch.cat([train_x, validate_x])
        pred = posterior_likelihood(posterior_model(domain))
        
        fig, ax = plt.subplots(1, 1, figsize=(15, 4))
        lower, upper = pred.confidence_region()
        
        ax.plot(train_x.numpy(), train_y.numpy(), 'k.', label="Training Data")
        
        ax.plot(domain.numpy(), pred.mean.numpy(), label='Predictive Mean')

        ax.plot(validate_x.numpy(), validate_y.numpy(), 'g.', label="Test Data")
        
        ax.fill_between(domain.numpy(), lower.numpy(), upper.numpy(), color='gray',
                        alpha=0.5, label='Predictive Confidence Bands')
        
        ax.set_title("Spectral Mixture Kernel Forecast", size=15)
        ax.legend(loc='lower left', fontsize=16, facecolor='white', framealpha=0.8, frameon=True)
        
        #fig.savefig('figs/sm_nee_forecast22.png')
    
    
if __name__ == '__main__':
    
    test_spectral_mixture()
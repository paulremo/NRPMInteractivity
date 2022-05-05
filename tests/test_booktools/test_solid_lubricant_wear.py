import pytest
from scipy import stats
import numpy as np

# import module
from nrpmint.booktools import solid_lubricant_wear

@pytest.mark.parametrize(
    'Dist_Vlim, E_Vlim, CoV_Vlim, Dist_KH, E_KH, CoV_KH, Dist_alpha, E_alpha, CoV_alpha, Dist_MU, E_MU, CoV_MU, '
    'E_nrev, Rev_per_hour, Pf_true', [
        ('LogNormal', 6.5e-8, 0.2, 'LogNormal', 4e-7, 0.66, 'LogNormal', 0.018, 0.2, 'LogNormal', 1.2, 0.2, 1, 1, None),
        ('LogNormal', 6.5e-8, 0.2, 'LogNormal', 4e-18, 0.66, 'LogNormal', 0.018, 0.2, 'LogNormal', 1.2, 0.2, 245e+6, 1000, None),
        ('Gumbel', 6.5e-8, 0.2, 'Normal', 4e-18, 0.66, 'LogNormal', 0.018, 0.2, 'LogNormal', 1.2, 0.2, 245e+6, 1000, None)
    ]
)
def test_running_model(unirv, multirv, Dist_Vlim, E_Vlim, CoV_Vlim, Dist_KH, E_KH, CoV_KH, Dist_alpha, E_alpha,
                       CoV_alpha, Dist_MU, E_MU, CoV_MU, E_nrev, Rev_per_hour, Pf_true):
    """
    Tests whether the model can be run with the provided model_wrapper and asserts the analytical results, where
    available.
    """
    reliability_analysis = solid_lubricant_wear.model_wrapper(Dist_Vlim=Dist_Vlim, E_Vlim=E_Vlim, CoV_Vlim=CoV_Vlim,
                                                              Dist_KH=Dist_KH, E_KH=E_KH, CoV_KH=CoV_KH,
                                                              Dist_alpha=Dist_alpha, E_alpha=E_alpha,
                                                              CoV_alpha=CoV_alpha, Dist_MU=Dist_MU, E_MU=E_MU,
                                                              CoV_MU=CoV_MU, E_nrev=E_nrev, Rev_per_hour=Rev_per_hour)



    if Pf_true == None:
        # failure probability not provided, compute it

        # init
        corr_KH_alpha = 0.5

        if Dist_Vlim == 'LogNormal' and Dist_KH == 'LogNormal' and Dist_alpha == 'LogNormal' and Dist_MU == 'LogNormal':
            # analytical solution available, if all distributions are LogNormal
            KH_dist = unirv(Dist_KH, E_KH, CoV_KH)
            alpha_dist = unirv(Dist_alpha, E_alpha, CoV_alpha)
            if corr_KH_alpha == 0:
                # variance of product of KH and alpha
                mu_KH = np.log(KH_dist.dist.__dict__['kwds']['scale'])
                sigma_KH = KH_dist.dist.__dict__['kwds']['s']
                mu_alpha = np.log(alpha_dist.dist.__dict__['kwds']['scale'])
                sigma_alpha = alpha_dist.dist.__dict__['kwds']['s']
                # parameters of KH*alpha
                mu_alpha_times_KH = mu_KH + mu_alpha
                sigma_alpha_times_KH = np.sqrt(sigma_KH**2 + sigma_alpha**2)
                # moments
                covar_KH_alpha = 0
                var_KH_times_alpha = (np.exp(sigma_alpha_times_KH**2)-1)*np.exp(2*mu_alpha_times_KH + sigma_alpha_times_KH**2)
            else:
                # covariance of KH and alpha as well as the variance of their product cannot be computed analytically
                # from the copula correlation
                joint_dist = multirv([KH_dist, alpha_dist], corrmat=[[1, corr_KH_alpha], [corr_KH_alpha, 1]])
                joint = joint_dist.rvs(10 ** 4)
                # moments
                covar_KH_alpha = np.cov(joint.T)[0,1]
                var_KH_times_alpha = np.var(joint[:, 0] * joint[:, 1])

            mean_x1 = E_Vlim
            mean_x2 = E_nrev * Rev_per_hour * (E_KH * E_alpha + covar_KH_alpha)
            CoV_x1 = CoV_Vlim
            CoV_x2 = np.sqrt(var_KH_times_alpha * (E_nrev * Rev_per_hour) ** 2) / mean_x2
            # equation for analytical solution from handbook
            Pf_true = stats.norm.cdf(
                (np.log(E_MU) - np.log(mean_x1/mean_x2) + 0.5*(np.log(CoV_x1**2+1) - np.log(CoV_x2**2+1) - np.log(CoV_MU**2+1)))/
                (np.sqrt(np.log(CoV_x1**2+1) + np.log(CoV_x2**2+1) +np.log(CoV_MU**2+1)))
            )
        else:
            # sampling-based solution required
            Vlim_dist = unirv(Dist_Vlim, E_Vlim, CoV_Vlim)
            KH_dist = unirv(Dist_KH, E_KH, CoV_KH)
            alpha_dist = unirv(Dist_alpha, E_alpha, CoV_alpha)
            MU_dist = unirv(Dist_MU, E_MU, CoV_MU)

            corrmat = np.eye(4)
            corrmat[1,2] = corr_KH_alpha
            corrmat[2,1] = corr_KH_alpha

            x_dist = multirv([Vlim_dist, KH_dist, alpha_dist, MU_dist], corrmat=corrmat)
            x = x_dist.rvs(10 ** 6)

            Pf_true = np.mean((x[:,0]-x[:,3]*x[:,1]*x[:,2]*E_nrev*Rev_per_hour)<0)

    assert reliability_analysis.Pf == pytest.approx(Pf_true, rel=5e-1)
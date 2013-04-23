"""
Determine whether constraints are active for a particular trading period
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def HVDC_Constraint(series, energy_price_send="", energy_price_receive="",
                    res_price="", abs_tol=None, rel_tol=None, min_split=10):
    """ 
    Determine whether an HVDC constraint is active within the system
    
    Parameters
    ----------
    series : The Pandas DF series (i.e. a single entry)
    energy_price : The energy price column name
    res_price : The reserve price column name
    inverse : Whether the inverse should be applied (e.g. multiply by -1)
    abs_tol : What absolute tolerance should be applied to the dataset
    rel_tol : What relative tolerance should be applied
    minimium_split : The minimum split required to attribute towards reserve
                     binding upon the system.
                     
    Returns
    -------
    constraint : True if constraint is binding, false otherwise
    """
    
    epr_send = series[energy_price_send]
    epr_rece = series[energy_price_receive]
    rpr = series[res_price]
    
    split = epr_rece - epr_send
    if split <= min_split:
        return False
    else:
        if abs_tol:
            return True if abs(split - rpr) <= abs_tol else False
        elif rel_tol:
            return True if abs(split - rpr) <= rel_tol * epr_send else False
        else:
            raise ValueError("Either abs_tol or rel_tol must be specified")
            
def constraint_plot(master_set, island="NI", inverse=False, min_split=10):
    """
    Construct a scatter plot constrained vs unconstrained reserves
    """
    
    cname = "%s Constraint" % island
    rname = "%s Reserve Price" % island
    ename = "Price Split"
    
    if inverse:
        subset = master_set.le_mask(ename, min_split*-1)
    else:
        subset = master_set.ge_mask(ename, min_split)
    
    x1 = subset.eq_mask(cname, True)[ename]
    y1 = subset.eq_mask(cname, True)[rname]
    
    x2 = subset.eq_mask(cname, False)[ename]
    y2 = subset.eq_mask(cname, False)[rname]
    
    if inverse:
        x1 = x1 * -1
        x2 = x2 * -1
    
    fig, axes = plt.subplots(1, figsize=(16,9))
    axes.scatter(x2, y2, marker='x', label="Unconstrained Periods", alpha=0.8, c='grey')
    axes.scatter(x1, y1, marker='o', label="Constrained Periods", c='k')

    axes.set_xlabel("%s Price Split [$/MWh]" % island)
    axes.set_ylabel(rname + ' [$/MWh]')
    axes.set_xlim(0, x1.max())
    axes.set_ylim(0, y1.max())
    axes.grid()
    axes.grid(axis='y')
    axes.legend()
    
    return fig, axes
    
    
def CCGT_Constraint(series, eprice="", oprice="", rprice="", abs_tol=None, 
                    rel_tol=None, min_split=10):
                    
    ep = series[eprice]
    op = series[oprice]
    rp = series[rprice]
    sp = ep - op
    
    if sp <= min_split:
        return False
    else:
        return True if np.abs(sp - rp) <= abs_tol else False
        
def CCGT_Offer_Plot(df):
    
    fig, axes = plt.subplots(1, figsize=(16,9))
    
    df = df.eq_mask("CCGT Constraint", True)
    
    x = df["Offer Price Split"]
    y = df["NI Reserve Price"]
    
    axes.scatter(x, y, marker='o', c='k')
    axes.set_xlim(0, x.max())
    axes.set_ylim(0, y.max())
    axes.set_xlabel("Energy Price - Offer Price [$/MWh]")
    axes.set_ylabel("North Island Reserve Price [$/MWh]")
    axes.grid()
    
    return fig, axes
    
def constraint_cdf(df, island="NI", measure=""):
    """
    Construct a cumulative distribution function to measure the
    occurrence of constraints against a measured variable.
    
    Parameters
    ----------
    df : The DataFrame to be measured
    island : What island the constraint should be determined for
    measure : The column it should be measured against
    
    Returns
    -------
    Series : A series containing the CDF for the function
    """
    
    cname = " ".join([island, "Constraint"])
    dfc = df.eq_mask(cname, True)[measure]
    
    binrange= np.arange(dfc.min(), dfc.max(), 1)
    hi, be = np.histogram(dfc, binrange)
    hi_norm = 1 - np.cumsum(1. * hi / hi.sum())
    return pd.Series(hi_norm, index=be[:-1])
    
def conditional_prob(df, island="NI", measure="", step=1, how='ge'):
    """
    Construct a conditional probability distribution using cumulative functions
    the how method may be specified (ge, lt, le, eq, gt, ne) to see the 
    conditional probability of a particular measure given constraints.
    
    E.g. Determine P(Constraint | Measure) for a range of measures.
    
    Parameters
    ----------
    df : The dataframe for which te conditional probability is desired
    island : What island the constraint should be tested for
    measure : What measure should be assessed
    step : Step size of measure to be used
    how : Which method ot apply to the cumulative frequency assessment
    
    Returns
    -------
    conditional_probability : The conditional probability given that
        the how condition has been met on the measure
    """
    
    
    cname = " ".join([island, "Constraint"])
    dfa = df[measure]
    dfc = df.eq_mask(cname, True)[measure]  
    
    binrange = np.arange(dfa.min(), dfa.max()+step, step)
    
    cp = cumul_frequency_assessment(dfc, dfa, binrange, how=how)
    return cp.sort_index()
    
    
    
def cumul_frequency_assessment(s1, s2, binrange, how='ge'):
    """Iterate over a binrange and assess the conditional probability
    for different levels
    
    NOTE: This is quite slow, can definitely make algorithmic speed
    improvements here but it's working so I'm leaving until another day
    """
    f = ( 1. * s1.mask(b, how=how).count() / s2.mask(b, how=how).count() 
          for b in binrange)
    return pd.Series(f, index=binrange)
        

    
    
if __name__ == '__main__':
    pass

    
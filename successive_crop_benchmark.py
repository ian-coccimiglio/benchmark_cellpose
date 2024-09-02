#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 00:43:57 2024

@author: ian
"""
from cellpose import models
from time import perf_counter
from skimage.io import imread
import os
from collections import defaultdict
import numpy as np
import logging
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import PercentFormatter

logging.basicConfig(level=logging.WARNING)

crop_path = "images/"
image_names = sorted(os.listdir(crop_path))
image_paths = [
    os.path.join(crop_path, image_name) for image_name in image_names
]

homedir = os.path.expanduser("~")
model_name = "cyto3"
diam = 0


def successive_crop(image_paths, model_name, diam, useGPU, n=5):
    """
    Runs benchmark analysis on a series of image paths

    Parameters
    ----------
    image_paths : LIST
        List of images
    model_name : STR
        Specific Model name
    diam : INT | FLOAT
        Diameter Input for Cellpose
    useGPU : BOOL
        Use GPU?
    n : INT, optional
        Number of repeats per image. The default is 5.

    Returns
    -------
    results : Dictionary
        Dictionary mapping image to results/outputs

    """
    print("Running successive image crop analysis")
    results = defaultdict(list)

    for enum, image_path in enumerate(image_paths):
        area = []
        im = imread(image_path)
        area = im.size
        sample_name = os.path.splitext(os.path.basename(image_path))[0]
        calculation_time = []
        for i in range(0, n):
            before = perf_counter()
            mod = models.Cellpose(gpu=useGPU, model_type="cyto3")
            masks, flow, style, est_diam = mod.eval(
                im, diameter=diam, channels=[0, 0]
            )
            after = perf_counter()
            calculation_time.append(after - before)
            print(
                f"Time: {os.path.splitext(image_path)[0]}: {round(after-before,2)}s"
            )
        results[sample_name].append(area)
        results[sample_name].append(model_name)
        results[sample_name].append(est_diam)
        results[sample_name].append(len(np.unique(masks)))
        results[sample_name].append(calculation_time)
    return results


def construct_dataframe(results):
    """
    Creates the dataframe from generated results

    Parameters
    ----------
    results : Dictionary
        Dictionary of results given by successive_crop

    Returns
    -------
    df : Dataframe
        Dataframe generated by the dictionary, expanded over n_repeats.

    """
    df = (
        pd.DataFrame()
        .from_dict(
            results,
            orient="index",
            columns=[
                "Area",
                "Model",
                "Diameter",
                "Masks",
                "Calculation_Time",
            ],
        )
        .explode("Calculation_Time")
    )
    df["Length"] = np.sqrt(df["Area"])
    return df


# Change `n` if you want to estimate the robustness.
GPU = False
results_cpu = successive_crop(
    image_paths,
    model_name=model_name,
    diam=diam,
    useGPU=GPU,
    n=1,
)
df_cpu = construct_dataframe(results_cpu)

GPU = True
results = defaultdict(list)
results_gpu = successive_crop(
    image_paths,
    model_name=model_name,
    diam=diam,
    useGPU=GPU,
    n=1,
)
df_gpu = construct_dataframe(results_gpu)

df = pd.concat(
    [df_cpu, df_gpu],
    keys=("CPU", "GPU"),
    names=["Processor", "Iteration"],
)

plt.figure(figsize=(15, 8))

sns.set(font_scale=1.2)
ax = sns.lineplot(
    df,
    x="Length",
    y="Calculation_Time",
    hue="Processor",
    err_style="bars",
    errorbar="sd",
)


def make_text(calc_time, length, neg):
    if neg == False:
        pos = calc_time + 5
    else:
        pos = calc_time - 5
    plt.text(
        x=length,
        y=pos,
        s=f"{np.round(calc_time, 2)}s",
        horizontalalignment="center",
    )


plt.ylim([-10, 120])

for proc in df.index.get_level_values(0).unique():
    gdf = df.loc[proc][["Calculation_Time", "Length"]]
    for e, (calc_time, length) in enumerate(
        zip(gdf["Calculation_Time"], gdf["Length"])
    ):
        if proc == "GPU":
            make_text(calc_time, length, neg=True)
        else:
            make_text(calc_time, length, neg=False)

plt.savefig("figures/GPU_vs_CPU.png")


percentage_improvement = df_gpu["Calculation_Time"].div(
    df_cpu["Calculation_Time"]
)
#%%
fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(15, 8))
ax.plot(df_gpu["Length"], percentage_improvement)
ax.set_title("GPU Relative to CPU")
ax.set_ylabel("GPU Evaluation time")
ax.set_xlabel("Image Length (pixels)")
ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set_ylim([0, 1])
plt.savefig("figures/Percentage_Improvement.png")

# Saving results
df.to_csv(f"results/Successive_Crop_Results_{model_name}.csv")

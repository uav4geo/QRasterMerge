from __future__ import division, absolute_import
import warnings

import numpy as np
import rasterio
from rasterio.enums import ColorInterp, MaskFlags


def rgb_to_xyz(rgb):
    """Convert RGB to XYZ color space.
    
    Parameters
    ----------
    rgb : numpy.ndarray
        RGB array with shape (3, height, width) and values in [0, 1]
        
    Returns
    -------
    numpy.ndarray
        XYZ array with same shape as input
    """
    # Apply gamma correction (sRGB to linear RGB)
    mask = rgb > 0.04045
    linear_rgb = np.where(mask, np.power((rgb + 0.055) / 1.055, 2.4), rgb / 12.92)
    
    # RGB to XYZ transformation matrix (sRGB D65)
    transform_matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    
    # Reshape for matrix multiplication
    original_shape = linear_rgb.shape
    linear_rgb_reshaped = linear_rgb.reshape(3, -1)
    
    # Apply transformation
    xyz = transform_matrix @ linear_rgb_reshaped
    
    # Reshape back to original shape
    return xyz.reshape(original_shape)


def xyz_to_lab(xyz):
    """Convert XYZ to LAB color space.
    
    Parameters
    ----------
    xyz : numpy.ndarray
        XYZ array with shape (3, height, width)
        
    Returns
    -------
    numpy.ndarray
        LAB array with same shape as input
    """
    # D65 illuminant
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    
    # Normalize by illuminant
    fx = xyz[0] / xn
    fy = xyz[1] / yn
    fz = xyz[2] / zn
    
    # Apply LAB transformation
    delta = 6.0 / 29.0
    delta_cubed = delta ** 3
    delta_squared = delta ** 2
    
    def f_transform(t):
        mask = t > delta_cubed
        return np.where(mask, np.cbrt(t), t / (3 * delta_squared) + 4.0 / 29.0)
    
    fx_t = f_transform(fx)
    fy_t = f_transform(fy)
    fz_t = f_transform(fz)
    
    # Calculate LAB values
    L = 116 * fy_t - 16
    a = 500 * (fx_t - fy_t)
    b = 200 * (fy_t - fz_t)
    
    return np.stack([L, a, b])


def lab_to_lch(lab):
    """Convert LAB to LCH color space.
    
    Parameters
    ----------
    lab : numpy.ndarray
        LAB array with shape (3, height, width)
        
    Returns
    -------
    numpy.ndarray
        LCH array with same shape as input
    """
    L, a, b = lab[0], lab[1], lab[2]
    
    # Calculate chroma and hue
    C = np.sqrt(a**2 + b**2)
    H = np.arctan2(b, a)
    
    # Convert hue from radians to degrees and ensure [0, 360)
    H_degrees = np.degrees(H)
    H_degrees = np.where(H_degrees < 0, H_degrees + 360, H_degrees)
    
    return np.stack([L, C, H_degrees])


def lch_to_lab(lch):
    """Convert LCH to LAB color space.
    
    Parameters
    ----------
    lch : numpy.ndarray
        LCH array with shape (3, height, width)
        
    Returns
    -------
    numpy.ndarray
        LAB array with same shape as input
    """
    L, C, H_degrees = lch[0], lch[1], lch[2]
    
    # Convert hue from degrees to radians
    H_radians = np.radians(H_degrees)
    
    # Calculate a and b
    a = C * np.cos(H_radians)
    b = C * np.sin(H_radians)
    
    return np.stack([L, a, b])


def lab_to_xyz(lab):
    """Convert LAB to XYZ color space.
    
    Parameters
    ----------
    lab : numpy.ndarray
        LAB array with shape (3, height, width)
        
    Returns
    -------
    numpy.ndarray
        XYZ array with same shape as input
    """
    L, a, b = lab[0], lab[1], lab[2]
    
    # D65 illuminant
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    
    # Calculate intermediate values
    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    
    # Apply inverse LAB transformation
    delta = 6.0 / 29.0
    delta_cubed = delta ** 3
    delta_squared = delta ** 2
    
    def f_inverse(t):
        mask = t > delta
        return np.where(mask, t**3, 3 * delta_squared * (t - 4.0 / 29.0))
    
    x = xn * f_inverse(fx)
    y = yn * f_inverse(fy)
    z = zn * f_inverse(fz)
    
    return np.stack([x, y, z])


def xyz_to_rgb(xyz):
    """Convert XYZ to RGB color space.
    
    Parameters
    ----------
    xyz : numpy.ndarray
        XYZ array with shape (3, height, width)
        
    Returns
    -------
    numpy.ndarray
        RGB array with same shape as input, values in [0, 1]
    """
    # XYZ to RGB transformation matrix (sRGB D65)
    transform_matrix = np.array([
        [ 3.2404542, -1.5371385, -0.4985314],
        [-0.9692660,  1.8760108,  0.0415560],
        [ 0.0556434, -0.2040259,  1.0572252]
    ])
    
    # Reshape for matrix multiplication
    original_shape = xyz.shape
    xyz_reshaped = xyz.reshape(3, -1)
    
    # Apply transformation
    linear_rgb = transform_matrix @ xyz_reshaped
    
    # Reshape back to original shape
    linear_rgb = linear_rgb.reshape(original_shape)
    
    # Apply gamma correction (linear RGB to sRGB)
    mask = linear_rgb > 0.0031308
    rgb = np.where(mask, 1.055 * np.power(linear_rgb, 1.0/2.4) - 0.055, 12.92 * linear_rgb)
    
    # Clamp to [0, 1] range
    rgb = np.clip(rgb, 0, 1)
    
    return rgb


def convert_arr(arr, src, dst):
    """Convert array between different color spaces.
    
    Parameters
    ----------
    arr : numpy.ndarray
        Input array with shape (3, height, width)
    src : str
        Source color space ('rgb' or 'lch')
    dst : str
        Destination color space ('rgb' or 'lch')
        
    Returns
    -------
    numpy.ndarray
        Converted array with same shape as input
    """
    src = src.lower() if isinstance(src, str) else str(src).lower()
    dst = dst.lower() if isinstance(dst, str) else str(dst).lower()
    
    if src == dst:
        return arr.copy()
    
    if src == 'rgb' and dst == 'lch':
        # RGB -> XYZ -> LAB -> LCH
        xyz = rgb_to_xyz(arr)
        lab = xyz_to_lab(xyz)
        return lab_to_lch(lab)
    elif src == 'lch' and dst == 'rgb':
        # LCH -> LAB -> XYZ -> RGB
        lab = lch_to_lab(arr)
        xyz = lab_to_xyz(lab)
        return xyz_to_rgb(xyz)
    else:
        raise ValueError(f"Unsupported color space conversion: {src} to {dst}")


class ColorSpace:
    rgb = 'rgb'
    lch = 'lch'


def reshape_as_image(arr):
    """raster order (bands, rows, cols) -> image (rows, cols, bands)

    TODO Use rasterio.plot.reshape_as_image in rasterio 0.36?
    """
    return np.swapaxes(np.swapaxes(arr, 0, 2), 0, 1)


def reshape_as_raster(arr):
    """image order (rows, cols, bands) -> rasterio (bands, rows, cols)

    TODO Use rasterio.plot.reshape_as_image in rasterio 0.36?
    """
    return np.swapaxes(np.swapaxes(arr, 2, 0), 2, 1)


def cs_forward(arr, cs='rgb'):
    """ RGB (any dtype) to whatevs
    """
    arrnorm_raw = arr.astype('float64') / np.iinfo(arr.dtype).max
    arrnorm = arrnorm_raw[0:3]
    cs = cs.lower()
    if cs == 'rgb':
        return arrnorm
    elif cs == 'lch':
        return convert_arr(arrnorm,
                           src=ColorSpace.rgb,
                           dst=ColorSpace.lch)
    

def cs_backward(arr, cs='rgb'):
    """ whatevs to RGB 8-bit
    """
    cs = cs.lower()
    if cs == 'rgb':
        return (arr * 255).astype('uint8')
    elif cs == 'lch':
        rgb = convert_arr(arr,
                          src=ColorSpace.lch,
                          dst=ColorSpace.rgb)
        return (rgb * 255).astype('uint8')


def raster_to_image(raster):
    """Make an image-ordered 8bit 3-band array
    from a rasterio source
    """
    with rasterio.open(raster) as src:
        arr = src.read(masked=True)
    return reshape_as_image(cs_forward(arr, 'RGB'))


def read_mask(dataset):
    """Get the dataset's mask

    Returns
    -------
    numpy.array

    Notes
    -----
    This function is no longer called by module code but we're going to
    continue to test it for a few future versions as insurance on the new
    implementation.

    """
    return dataset.dataset_mask()

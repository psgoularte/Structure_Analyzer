def generate_colormap():
    import numpy as np
    import matplotlib.pyplot as plt

    def create_colormap(values, cmap_name='viridis'):
        norm = plt.Normalize(vmin=min(values), vmax=max(values))
        colormap = plt.get_cmap(cmap_name)
        colors = colormap(norm(values))
        return colors

    def visualize_colormap(values, cmap_name='viridis'):
        colors = create_colormap(values, cmap_name)
        plt.figure(figsize=(8, 2))
        plt.imshow([colors], aspect='auto')
        plt.axis('off')
        plt.title(f'Colormap: {cmap_name}')
        plt.show()

    # Example usage
    if __name__ == "__main__":
        sample_values = np.linspace(0, 100, 10)
        visualize_colormap(sample_values)
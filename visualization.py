import matplotlib.pyplot as plt
import json
import math
import numpy as np

def paint_layout_to_ax(ax, layout_info):
    ax.add_patch(plt.Circle((0, 0), layout_info['plate_radius'], fill=True, linestyle='-', color='gray'))
    for id, marker in enumerate(layout_info['markers']):
        if (marker['elevated']): #draw a shadow
            ax.add_patch(plt.Circle(
                (marker['x'] + layout_info['marker_radius'] * 0.333, marker['y'] - layout_info['marker_radius'] * 0.333),
                layout_info['marker_radius'],
                fill=True,
                linestyle='-',
                color='black',
                alpha=0.25,
            ))
        ax.add_patch(plt.Circle((marker['x'], marker['y']), layout_info['marker_radius'], fill=True, linestyle='-', color='darkgray'))
        ax.annotate(id, (marker['x'], marker['y']))
 
    ax.set_xlim(-layout_info['plate_radius'] * 1.15, layout_info['plate_radius'] * 1.15)
    ax.set_ylim(-layout_info['plate_radius'] * 1.15, layout_info['plate_radius'] * 1.15)
    ax.set_aspect('equal')
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')

def paint_constellation_to_ax(ax, layout_info, constellation):
    def draw_lit_sphere(ax, x, y, radius, light_angle_deg=45, color=(0.7, 0.7, 0.9)):
        """
        I shall not tell a lie, claude wrote this part.
        It does look lovely and it's exactly what I wanted :D
        """
        n = 100
        xs = np.linspace(-1, 1, n)
        ys = np.linspace(-1, 1, n)
        xx, yy = np.meshgrid(xs, ys)
        zz2 = 1 - xx**2 - yy**2  # sphere height^2 at each point (in unit disk)
        mask = zz2 >= 0
        zz = np.sqrt(np.clip(zz2, 0, None))

        # light direction (unit vector), pointing somewhat "out of the page" too
        light_rad = np.radians(light_angle_deg)
        lx, ly, lz = np.cos(light_rad), np.sin(light_rad), 0.6
        norm = np.sqrt(lx**2 + ly**2 + lz**2)
        lx, ly, lz = lx / norm, ly / norm, lz / norm

        # normal at each point on the sphere surface is (xx, yy, zz) (unit, since x^2+y^2+z^2=1)
        shade = xx * lx + yy * ly + zz * lz
        shade = np.clip(shade, 0, None)
        shade[~mask] = 0

        # ambient + diffuse, add a small specular highlight
        ambient = 0.25
        diffuse = 0.75 * shade
        specular = 0.6 * (shade ** 20)  # tight highlight
        intensity = np.clip(ambient + diffuse + specular, 0, 1)

        img = np.zeros((n, n, 4))
        for c in range(3):
            img[..., c] = color[c] * intensity
        img[..., 3] = mask.astype(float)  # transparent outside the disk

        im = ax.imshow(img, extent=(x - radius, x + radius, y - radius, y + radius),
                        origin='lower', zorder=3, interpolation='bilinear')
        return im

    paint_layout_to_ax(ax, layout_info)
    for id, marker in enumerate(layout_info['markers']):
        if (id in constellation):
            # ax.add_patch(plt.Circle((marker['x'], marker['y']), layout_info['marker_radius'], fill=True, linestyle='-', color='white'))
            draw_lit_sphere(ax, marker['x'], marker['y'], layout_info['marker_radius'])
            ax.annotate(id, (marker['x'], marker['y']))

def show_layout(layout_json_path):
    assert layout_json_path[-5:] == '.json', f'Bad file type to visualization.show_layout, {layout_json_path}'
    # Read the json
    with open(layout_json_path, 'r') as f:
        data = json.load(f)
    # Make the diagram :)
    _, ax = plt.subplots(figsize=(7, 7))
    paint_layout_to_ax(ax, data)
    ax.set_title('Candidate layout at ' + layout_json_path)
    plt.tight_layout()
    plt.savefig(layout_json_path[:-5] + '.png', dpi=150)
    plt.show()

def show_constellations(layout_json_path, constellation_json_path):
    assert layout_json_path[-5:] == '.json', f'Bad file type to visualization.show_layout, {layout_json_path}'
    assert constellation_json_path[-5:] == '.json', f'Bad file type to visualization.show_layout, {constellation_json_path}'
    # Read the json
    with open(layout_json_path, 'r') as f:
        layout_data = json.load(f)
    with open(constellation_json_path, 'r') as f:
        constellation_data = json.load(f)
    # Make the diagram :)
    num_constellations = len(constellation_data['constellations'])
    num_cols = 3
    num_rows = math.ceil(num_constellations / num_cols)
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(num_cols * 4, num_rows * 4))
    for row in range(num_rows):
        for col in range(num_cols):
            ax = axes[row, col]
            ind = row * 3 + col
            if (ind >= num_constellations): break # when fewer than 3 in last row, don't write anything to that ax
            paint_constellation_to_ax(ax, layout_data, constellation_data['constellations'][ind])
            ax.set_title(f'Constellation {ind}')
    fig.suptitle('Constellation set')
    plt.tight_layout()
    plt.savefig(constellation_json_path[:-5] + '.png', dpi=150)
    plt.show()

def main():
    # Make your own visuals here, then call this file!
    # Something that may trip you up: plt.show() consumes fig, so if you want to save it, call plt.savefig(...) first.
    # show_constellations('artifacts/corvus_layout.json', 'artifacts/corvus_constellations.json')
    show_layout('artifacts/corvus_layout.json')
if __name__=='__main__':
    main()

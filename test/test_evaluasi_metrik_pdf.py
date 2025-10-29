import os
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from fpdf import FPDF

# ==== GENERATE DATA DUMMY: EMOTION & CLUSTERING ====
np.random.seed(8)
emotion_labels = ['happy', 'sad', 'angry', 'surprise', 'neutral', 'disgust', 'fear']
data_emotion = np.random.choice(emotion_labels, 200, p=[0.39, 0.20, 0.10, 0.05, 0.20, 0.03, 0.03])

dist = dict(Counter(data_emotion))

# Cluster dummy
n_clusters = 5
face_cluster_true = np.repeat(np.arange(n_clusters), 40)
face_cluster_pred = np.random.permutation(np.repeat(np.arange(n_clusters), 40))

# ==== VISUALISASI & SIMPAN GAMBAR ====
def save_emotion_bar(dist, filename):
    plt.figure(figsize=(6,4))
    plt.bar(dist.keys(), dist.values(), color='skyblue')
    plt.title('Distribusi Deteksi Emosi')
    plt.ylabel('Jumlah')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def save_confusion_matrix(true, pred, filename):
    from sklearn.metrics import confusion_matrix
    import seaborn as sns
    cm = confusion_matrix(true, pred, labels=np.unique(true))
    plt.figure(figsize=(5,4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='rocket', xticklabels=np.unique(true), yticklabels=np.unique(true))
    plt.ylabel('True label')
    plt.xlabel('Prediksi')
    plt.title('Clustering Confusion Matrix')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Simpan grafik bar emosi & matrix cluster
gambar_emosi = "chart_emotion_bar.png"
gambar_cluster = "chart_cluster_matrix.png"
save_emotion_bar(dist, gambar_emosi)
save_confusion_matrix(face_cluster_true, face_cluster_pred, gambar_cluster)

# ==== METRIK EVALUASI ====
def calc_purity(true, pred):
    from sklearn.metrics.cluster import contingency_matrix
    matrix = contingency_matrix(true, pred)
    return np.sum(np.amax(matrix, axis=0)) / np.sum(matrix)

purity = calc_purity(face_cluster_true, face_cluster_pred)

# ==== GENERATE PDF LAPORAN ====
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Laporan Evaluasi Sistem EmongDeepFace', 0, 1, 'C')
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()

# Ringkasan
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 8, """
Laporan ini berisi hasil simulasi evaluasi sistem:
- Distribusi emosi hasil prediksi model
- Metrik clustering wajah (dummy)
- Visualisasi otomatis
""")
pdf.ln(2)

pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, 'Distribusi Emosi (Dummy)', 0, 1)
pdf.image(gambar_emosi, x=20, w=160)
pdf.ln(3)
pdf.set_font('Arial', '', 11)
for e, n in dist.items():
    pdf.cell(40, 8, f'{e.capitalize():<14}: {n} kasus', ln=1)
pdf.ln(3)

pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, 'Metrik Clustering Wajah', 0, 1)
pdf.image(gambar_cluster, x=35, w=120)
pdf.set_font('Arial', '', 11)
pdf.ln(2)
pdf.cell(0,8, f'Clustering Dummy Purity Score: {purity:.3f}', ln=1)

# Simpan PDF
dest_pdf = "laporan_evaluasi_emongdeepface.pdf"
pdf.output(dest_pdf)

print(f"✅ Laporan PDF berhasil dibuat: {dest_pdf}")

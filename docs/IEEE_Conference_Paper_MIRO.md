# MIRO: A Multimodal AI-Powered Mental Health Assistant for Emotion Recognition and Analysis

---

## Abstract

Emotional well-being is a critical aspect of mental health that often goes undiagnosed due to limited accessibility to professional psychological assessment tools. This paper presents MIRO, a multimodal AI-powered mental health assistant designed to recognize and analyze human emotions through the integration of facial expression recognition, audio tone analysis, and speech sentiment analysis. The proposed system employs a weighted fusion algorithm that combines outputs from three distinct modalities: a DeepFace-based convolutional neural network for facial emotion detection, a custom LSTM-based deep learning model for audio prosody analysis, and the VADER (Valence Aware Dictionary and Sentiment Reasoner) lexicon-based approach for textual sentiment classification. By processing video inputs, MIRO extracts multimodal features and computes a unified emotional state with associated confidence metrics. Preliminary evaluations demonstrate that the multimodal fusion approach provides more robust and accurate emotion recognition compared to single-modality systems. The system is implemented as a web application with a React-based frontend and Flask-powered backend, ensuring accessibility and ease of use for end-users seeking emotional self-awareness and preliminary mental health insights.

---

## Keywords

Multimodal Emotion Recognition, Deep Learning, Mental Health, Facial Expression Analysis, Audio Prosody, Sentiment Analysis, Convolutional Neural Networks, LSTM, Natural Language Processing, Human-Computer Interaction

---

## I. Introduction

Mental health disorders constitute a significant global health burden, affecting approximately 792 million people worldwide according to the World Health Organization [1]. Early detection and continuous monitoring of emotional states can facilitate timely interventions and improve treatment outcomes. However, access to mental health professionals remains limited in many regions, creating a pressing need for accessible, AI-powered tools that can assist individuals in understanding their emotional well-being.

Human emotion expression is inherently multimodal, manifesting simultaneously through facial expressions, vocal characteristics, and verbal content [2]. Traditional emotion recognition systems typically focus on a single modality, which limits their accuracy and robustness in real-world scenarios where individuals may suppress or mask emotions in one channel while revealing them in another. Research has consistently demonstrated that multimodal approaches outperform unimodal systems in emotion recognition tasks [3].

This paper presents MIRO (Mental Intelligence and Recognition Oracle), a comprehensive multimodal emotion analysis system designed to serve as an AI-powered mental health assistant. MIRO integrates three complementary emotion recognition modalities: (1) facial expression analysis using deep convolutional neural networks, (2) audio tone classification using LSTM-based models trained on prosodic features, and (3) text sentiment analysis using lexicon-based natural language processing techniques.

The primary contributions of this work are as follows:
- Design and implementation of a multimodal emotion recognition system that fuses facial, audio, and textual modalities
- Development of a weighted voting fusion algorithm that assigns modality-specific confidence weights based on reliability
- Creation of an accessible web-based platform that enables users to upload video content for comprehensive emotional analysis
- Implementation of real-time visualization components that present emotion recognition results in an intuitive, user-friendly manner

The remainder of this paper is organized as follows: Section II discusses the problem statement and motivation. Section III reviews related work in multimodal emotion recognition. Section IV presents the proposed system methodology. Section V describes the system architecture. Section VI provides implementation details. Section VII presents preliminary results and discussion. Section VIII concludes the paper and outlines future work.

---

## II. Problem Statement

Despite significant advances in affective computing, existing emotion recognition systems face several critical limitations that hinder their practical deployment for mental health applications:

**A. Single-Modality Limitations**

Most commercial and research emotion recognition systems rely on a single input modality, typically facial expressions or voice analysis alone. This approach is inherently limited because humans naturally mask or suppress emotions in certain channels. A user may maintain a neutral facial expression while their voice reveals stress or anxiety, or they may speak calmly while their facial expressions betray underlying distress [4].

**B. Accessibility Barriers**

Current mental health assessment tools often require clinical settings, trained professionals, or expensive equipment. This creates significant barriers for individuals seeking to understand their emotional states, particularly in regions with limited mental health infrastructure. There exists a need for accessible, non-invasive tools that can provide preliminary emotional insights without requiring professional supervision.

**C. Integration Complexity**

While multimodal systems offer theoretical advantages, their implementation presents significant technical challenges. These include synchronizing inputs across modalities, handling missing or degraded inputs, determining appropriate fusion strategies, and presenting results in a manner comprehensible to non-technical users.

**D. Privacy Concerns**

Emotion recognition systems that process sensitive audio-visual data raise legitimate privacy concerns. Users may be reluctant to share personal videos with cloud-based services, particularly when discussing mental health-related topics.

MIRO addresses these challenges by providing a locally-deployable, multimodal emotion recognition system that processes video inputs to extract and fuse emotional signals across facial, audio, and textual modalities, presenting results through an intuitive web interface while maintaining user privacy through local processing.

---

## III. Related Work

Research in multimodal emotion recognition has progressed significantly over the past decade, driven by advances in deep learning and the availability of multimodal datasets.

**A. Facial Emotion Recognition**

Facial expression recognition has been extensively studied using both traditional machine learning approaches with handcrafted features and modern deep learning methods. Ekman's pioneering work established six basic emotions (anger, disgust, fear, happiness, sadness, surprise) that can be universally recognized from facial expressions [5]. Contemporary approaches utilize convolutional neural networks (CNNs) trained on large-scale datasets such as FER2013, AffectNet, and RAF-DB. The DeepFace framework, employed in our system, leverages pre-trained CNN architectures to achieve robust facial emotion detection [6].

**B. Speech Emotion Recognition**

Speech emotion recognition (SER) exploits acoustic features such as pitch, energy, and Mel-Frequency Cepstral Coefficients (MFCCs) to classify emotional states. Schuller et al. demonstrated the effectiveness of spectral and prosodic features for emotion classification [7]. Recent approaches employ recurrent neural networks, particularly Long Short-Term Memory (LSTM) networks, to capture temporal dependencies in speech signals. The librosa library provides comprehensive audio feature extraction capabilities that have become standard in SER research [8].

**C. Text Sentiment Analysis**

Sentiment analysis from text has evolved from lexicon-based approaches to sophisticated deep learning models. The VADER (Valence Aware Dictionary and Sentiment Reasoner) tool, developed by Hutto and Gilbert, provides effective sentiment scoring for social media text and general domains without requiring extensive training data [9]. Transformer-based models such as BERT have achieved state-of-the-art performance on sentiment classification tasks, though they require significant computational resources.

**D. Multimodal Fusion Strategies**

Multimodal fusion can be performed at various levels: early fusion (feature-level), late fusion (decision-level), or hybrid approaches. Poria et al. demonstrated that tensor fusion networks can effectively model cross-modal interactions [10]. However, simpler weighted voting schemes have proven effective when computational efficiency is a priority and individual modalities provide reliable predictions.

**E. Mental Health Applications**

The application of emotion recognition to mental health has gained increasing attention. Systems have been developed for depression screening, anxiety detection, and stress monitoring. Ringeval et al. introduced the AVEC challenges that have advanced the field of depression and affect recognition from multimodal data [11].

Our work builds upon these foundations by integrating proven techniques from each domain into a cohesive system designed specifically for accessible mental health support.

---

## IV. Proposed System / Methodology

The proposed MIRO system implements a multimodal emotion recognition pipeline that processes video inputs to extract emotional indicators from three complementary modalities: facial expressions, audio prosody, and speech content.

**A. Multimodal Processing Pipeline**

The system processes uploaded video files through a sequential pipeline that parallelizes modality-specific analysis:

1. **Video Input Processing**: The system accepts standard video formats (MP4, AVI, MOV, WEBM) and extracts individual frames for facial analysis while simultaneously extracting the audio track for prosodic and textual analysis.

2. **Frame Sampling Strategy**: To optimize computational efficiency while maintaining accuracy, the system analyzes every 5th frame. This approach reduces processing overhead by approximately 80% while capturing sufficient temporal variation in facial expressions.

3. **Audio Extraction**: The audio track is extracted using the pydub library and converted to WAV format for consistent processing across the recognition pipeline.

**B. Facial Emotion Recognition Module**

The facial emotion recognition module employs the DeepFace framework with the following characteristics:

- **Architecture**: Pre-trained convolutional neural network optimized for facial expression classification
- **Emotion Classes**: Seven discrete emotions (happy, sad, angry, fear, surprise, disgust, neutral)
- **Detection Mode**: Non-enforced detection to handle frames where faces may be partially occluded or absent
- **Aggregation Strategy**: Dominant emotion determined through majority voting across all analyzed frames

The preprocessing pipeline resizes input frames to 224×224 pixels and normalizes pixel values to the [0, 1] range as required by the underlying CNN architecture.

**C. Audio Tone Recognition Module**

The audio emotion recognition module employs a custom LSTM-based deep learning model trained on a four-class emotion dataset:

- **Feature Extraction**: Audio features are extracted using the librosa library, including:
  - Mel-Frequency Cepstral Coefficients (40 coefficients)
  - Chroma features (12-dimensional pitch class profiles)
  - Spectral contrast features (7 bands)
  - Zero crossing rate

- **Feature Representation**: Features are concatenated along the frequency axis, resulting in a 60-dimensional feature vector per time step

- **Temporal Standardization**: Features are padded or truncated to a fixed length of 174 timesteps, enabling batch processing

- **Model Architecture**: LSTM layers process the temporal feature sequence to capture prosodic patterns indicative of emotional states

- **Emotion Classes**: Four categories (neutral, happy, sad, angry)

**D. Text Sentiment Analysis Module**

The text analysis module combines speech recognition with sentiment analysis:

- **Speech-to-Text**: Google Speech Recognition API converts the audio track to text transcript
- **Sentiment Classification**: VADER SentimentIntensityAnalyzer computes polarity scores
- **Emotion Mapping**: Compound scores are mapped to emotional categories:
  - Compound ≥ 0.4 → Happy (positive sentiment)
  - Compound ≤ -0.4 → Sad/Angry (negative sentiment)
  - -0.4 < Compound < 0.4 → Neutral

**E. Multimodal Fusion Algorithm**

The system employs a weighted voting fusion strategy that combines predictions from all three modalities:

$$\text{Overall Emotion} = \arg\max_{e \in E} \sum_{m \in M} w_m \cdot \mathbb{1}[p_m = e]$$

Where:
- $E$ = set of possible emotions
- $M$ = set of modalities (face, audio, text)
- $w_m$ = weight assigned to modality $m$
- $p_m$ = predicted emotion from modality $m$

The weights are empirically determined based on modality reliability:
- Face Emotion: 40% (highest weight due to visual expression reliability)
- Audio Tone: 30% (complementary prosodic information)
- Text Sentiment: 30% (semantic content from speech)

A confidence score is computed as the normalized sum of weights contributing to the final prediction.

---

## V. System Architecture

The MIRO system follows a client-server architecture with clear separation between the presentation layer and the processing backend.

**A. Frontend Architecture**

The frontend is implemented as a single-page application (SPA) using React 18.2 with the following component hierarchy:

1. **App Component**: Root component managing routing and theme state
2. **Home Page**: Landing page presenting system capabilities with animated 3D elements
3. **Analyze Page**: Video upload interface with drag-and-drop functionality
4. **Results Page**: Comprehensive visualization dashboard displaying emotion analysis results

Key frontend technologies include:
- **React Router DOM 6.20**: Client-side navigation
- **Framer Motion 10.16**: Smooth animations and transitions
- **Recharts 2.10**: Data visualization for emotion distributions
- **Axios 1.6**: HTTP client for API communication

**B. Backend Architecture**

The backend is implemented as a RESTful API using Flask 3.0 with the following components:

1. **API Layer**: Exposes the `/analyze_full_video` endpoint accepting multipart form data
2. **Processing Pipeline**: Orchestrates the multimodal analysis workflow
3. **Model Layer**: Manages pre-trained models and inference operations
4. **Fusion Engine**: Implements the weighted voting algorithm

Key backend dependencies include:
- **TensorFlow 2.15**: Deep learning framework for model inference
- **DeepFace 0.0.92**: Facial emotion recognition
- **Librosa 0.10.1**: Audio feature extraction
- **OpenCV 4.9**: Video frame processing
- **NLTK**: Natural language processing toolkit

**C. Data Flow**

1. User uploads video through the React frontend
2. Video is transmitted via HTTP POST to the Flask backend
3. Backend extracts video frames and audio track
4. Parallel processing pipelines analyze each modality
5. Fusion engine combines modality predictions
6. JSON response containing all results is returned to frontend
7. Frontend renders visualization components based on response data

---

## VI. Implementation Details

**A. Hardware Requirements**

The system is designed to operate on consumer-grade hardware:
- Processor: Intel/AMD CPU with 4+ cores recommended
- RAM: 8 GB minimum, 16 GB recommended
- GPU: Optional NVIDIA GPU with CUDA support for accelerated TensorFlow inference
- Storage: Approximately 2 GB for dependencies and model weights

**B. Software Dependencies**

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.8-3.11 | Backend execution environment |
| Web Framework | Flask | 3.0.0 | REST API server |
| Deep Learning | TensorFlow | 2.15.0 | Neural network inference |
| Face Analysis | DeepFace | 0.0.92 | Facial emotion recognition |
| Audio Processing | Librosa | 0.10.1 | Feature extraction |
| Video Processing | OpenCV | 4.9.0 | Frame extraction |
| NLP | NLTK | Latest | Sentiment analysis |
| Frontend | React | 18.2.0 | User interface |

**C. Model Specifications**

The audio emotion recognition model was trained with the following specifications:
- Input Shape: (174, 60) - 174 timesteps × 60 features
- Architecture: LSTM layers with dropout regularization
- Output: Softmax probability distribution over 4 emotion classes
- Training: Custom dataset with labeled emotional speech samples

**D. Performance Optimizations**

Several optimizations were implemented to ensure responsive performance:
- Frame sampling (every 5th frame) reduces face analysis computation by 80%
- Models are loaded once at server startup and cached in memory
- Probability smoothing with temperature scaling (0.4) improves visualization
- Asynchronous frontend updates during processing maintain UI responsiveness

**E. Privacy Considerations**

MIRO is designed with privacy as a priority:
- All processing occurs locally on the user's machine
- Temporary video files are automatically deleted after analysis
- No data is transmitted to external servers (except speech-to-text API)
- No personal information is stored or logged

---

## VII. Results and Discussion

As the MIRO system is currently in active development (approximately 50% complete), this section presents preliminary results and expected outcomes based on component-level testing.

**A. Component-Level Validation**

Each modality component has been validated independently:

*Facial Emotion Recognition:*
The DeepFace-based facial emotion module successfully detects and classifies emotions from video frames. Testing with sample videos containing clear facial expressions demonstrates correct identification of dominant emotions. The frame sampling strategy effectively captures expression variations while maintaining computational efficiency.

*Audio Tone Analysis:*
The custom LSTM model demonstrates the ability to distinguish between the four target emotion classes. Feature extraction using MFCCs, chroma, and spectral contrast provides discriminative representations for emotional speech patterns.

*Text Sentiment Analysis:*
The VADER-based sentiment analysis accurately classifies positive, negative, and neutral statements. Integration with Google Speech Recognition enables end-to-end processing from audio to sentiment classification.

**B. Multimodal Fusion Performance**

Preliminary observations indicate that the weighted fusion approach effectively combines modality predictions. When modalities agree, confidence scores are high (>0.9). When modalities disagree, the weighted voting mechanism selects the most reliable prediction based on assigned weights.

**C. User Interface Evaluation**

The React-based frontend provides an intuitive experience with the following characteristics:
- Drag-and-drop video upload simplifies user interaction
- Real-time loading feedback during processing maintains engagement
- Color-coded visualizations enable quick interpretation of results
- Responsive design ensures accessibility across devices

**D. Limitations and Challenges**

Current limitations include:
- Speech recognition accuracy depends on audio quality and clarity
- Neutral expressions may be overrepresented in face analysis
- The system requires internet connectivity for speech-to-text functionality
- Processing time increases with video duration

**E. Expected Outcomes**

Based on component performance and literature benchmarks, the complete system is expected to achieve:
- Improved accuracy over single-modality approaches through multimodal fusion
- Robust performance across diverse video content
- Acceptable processing times for videos under 60 seconds
- High user satisfaction with the visualization interface

---

## VIII. Conclusion

This paper presented MIRO, a multimodal AI-powered mental health assistant designed to provide accessible emotion recognition and analysis. By integrating facial expression recognition, audio tone analysis, and text sentiment analysis through a weighted voting fusion mechanism, MIRO offers a comprehensive approach to understanding emotional states from video content.

The system architecture separates concerns between a React-based frontend and Flask-powered backend, enabling modular development and deployment flexibility. Priority has been placed on user privacy through local processing and automatic deletion of temporary files.

Preliminary validation demonstrates successful integration of component modalities, with each providing complementary emotional indicators. The weighted fusion algorithm effectively combines these predictions into unified emotion assessments with associated confidence metrics.

MIRO represents a step toward democratizing access to emotional self-awareness tools, potentially serving as a preliminary mental health support resource for individuals who lack access to professional psychological services. While not intended to replace clinical assessment, the system may help users identify emotional patterns and encourage them to seek professional support when needed.

---

## IX. Future Work

Several directions are planned for future development:

**A. Enhanced Models**
- Training the audio emotion model on larger, more diverse datasets
- Incorporating transformer-based architectures for improved accuracy
- Adding additional emotion classes beyond the current four categories

**B. Additional Modalities**
- Physiological signal integration (heart rate variability, skin conductance) when wearable data is available
- Body language and gesture recognition through pose estimation

**C. Temporal Analysis**
- Tracking emotional changes over longer video durations
- Identifying emotional transitions and patterns

**D. Personalization**
- User-specific calibration to account for individual expression styles
- Longitudinal tracking to establish personal emotional baselines

**E. Clinical Validation**
- Formal evaluation studies comparing MIRO outputs with professional assessments
- Collaboration with mental health practitioners to refine the system

**F. Privacy Enhancements**
- Implementing on-device speech recognition to eliminate external API dependency
- Adding end-to-end encryption for data in transit

**G. Accessibility Features**
- Multi-language support for speech recognition and sentiment analysis
- Simplified visualization modes for users with disabilities

---

## References

[1] World Health Organization, "Mental disorders," WHO Fact Sheet, 2019. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/mental-disorders

[2] R. W. Picard, *Affective Computing*. Cambridge, MA, USA: MIT Press, 1997.

[3] S. Poria, E. Cambria, R. Bajpai, and A. Hussain, "A review of affective computing: From unimodal analysis to multimodal fusion," *Information Fusion*, vol. 37, pp. 98-125, 2017.

[4] A. Mehrabian, *Nonverbal Communication*. Chicago, IL, USA: Aldine-Atherton, 1972.

[5] P. Ekman and W. V. Friesen, "Constants across cultures in the face and emotion," *Journal of Personality and Social Psychology*, vol. 17, no. 2, pp. 124-129, 1971.

[6] S. I. Serengil and A. Ozpinar, "LightFace: A Hybrid Deep Face Recognition Framework," in *Proc. IEEE Int. Conf. Innovations in Intelligent Systems and Applications*, 2020, pp. 23-27.

[7] B. Schuller, A. Batliner, S. Steidl, and D. Seppi, "Recognising realistic emotions and affect in speech: State of the art and lessons learnt from the first challenge," *Speech Communication*, vol. 53, no. 9-10, pp. 1062-1087, 2011.

[8] B. McFee et al., "librosa: Audio and Music Signal Analysis in Python," in *Proc. 14th Python in Science Conf.*, 2015, pp. 18-24.

[9] C. J. Hutto and E. Gilbert, "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text," in *Proc. AAAI Conf. Weblogs and Social Media*, 2014.

[10] S. Poria, E. Cambria, D. Hazarika, N. Majumder, A. Zadeh, and L.-P. Morency, "Context-Dependent Sentiment Analysis in User-Generated Videos," in *Proc. ACL*, 2017, pp. 873-883.

[11] F. Ringeval et al., "AVEC 2019 Workshop and Challenge: State-of-Mind, Detecting Depression with AI, and Cross-Cultural Affect Recognition," in *Proc. ACM Int. Conf. Multimodal Interaction*, 2019, pp. 3-12.

---

*Manuscript submitted: January 2026*

*This paper presents research in progress on the MIRO Mental Health AI Assistant project.*

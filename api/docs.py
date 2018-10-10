import docmodels
import endpoints
import config

def build_docs(connection):
  # Main query endpoint
  papers = docmodels.Chapter("Paper search", "Search all bioRxiv papers.")
  query = papers.add_endpoint("Search", "/papers", "Retrieve a list of papers matching the given criteria.")
  query.add_argument("get", "query", "A search string to filter results based on their titles, abstracts and authors.", "")

  metric = query.add_argument("get", "metric", "Which field to use when sorting results.", "twitter")
  metric.add_values(["downloads", "twitter"])

  timeframe = query.add_argument("get", "timeframe", "How far back to look for the cumulative results of the chosen metric. (\"ytd\" and \"lastmonth\" are only available for the \"downloads\" metric.", "\"day\" for Twitter metrics, \"alltime\" for downloads.")
  timeframe.add_values(["alltime", "ytd", "lastmonth", "day", "week", "month", "year"])

  catfilter = query.add_argument("get", "category_filter", "An array of categories to which the results should be limited.", "[]")
  category_list = endpoints.get_categories(connection) # list of all article categories
  catfilter.add_values(category_list)

  query.add_argument("get", "page", "Number of the page of results to retrieve. Shorthand for an offset based on the specified page_size", 0)

  query.add_argument("get", "page_size", "How many results to return at one time. Capped at {}.".format(config.max_page_size_api), 20)

  query.add_example(
    "Top 3 downloaded papers, all time",
    "Using the \"downloads\" metric, get 3 papers ordered by their overall download count.",
    "/papers?metric=downloads&page_size=3&timeframe=alltime",
    """{
  "query": {
    "text_search": "",
    "timeframe": "alltime",
    "categories": [],
    "metric": "downloads",
    "page_size": 3,
    "current_page": 0,
    "final_page": 11138
  },
  "results": {
    "ids": [
      12345,
      12346,
      12347
    ],
    "items": [
      {
        "id": 12345,
        "metric": 166288,
        "title": "Example Paper Here: A compelling placeholder",
        "url": "https://www.biorxiv.org/content/early/2018/fake_url",
        "doi": "10.1101/00000",
        "collection": "cancer-biology",
        "first_posted": "19-09-18",
        "abstract": "This is where the abstract would go.",
        "authors": [
          "Richard Abdill",
          "Another Person"
        ]
      },
      {
        "id": 12346,
        "metric": 106169,
        "title": "Deep image reconstruction from human brain activity",
        "url": "https://www.biorxiv.org/content/early/2017/12/30/240317",
        "doi": "10.1101/240317",
        "collection": "neuroscience",
        "first_posted": "28-12-2017",
        "abstract": "Machine learning-based analysis of human functional magnetic resonance imaging (fMRI) patterns has enabled the visualization of perceptual content. However, it has been limited to the reconstruction with low-level image bases or to the matching to exemplars. Recent work showed that visual cortical activity can be decoded (translated) into hierarchical features of a deep neural network (DNN) for the same input image, providing a way to make use of the information from hierarchical visual features. Here, we present a novel image reconstruction method, in which the pixel values of an image are optimized to make its DNN features similar to those decoded from human brain activity at multiple layers. We found that the generated images resembled the stimulus images (both natural images and artificial shapes) and the subjective visual content during imagery. While our model was solely trained with natural images, our method successfully generalized the reconstruction to artificial shapes, indicating that our model indeed reconstructs or generates images from brain activity, not simply matches to exemplars. A natural image prior introduced by another deep neural network effectively rendered semantically meaningful details to reconstructions by constraining reconstructed images to be similar to natural images. Furthermore, human judgment of reconstructions suggests the effectiveness of combining multiple DNN layers to enhance visual quality of generated images. The results suggest that hierarchical visual information in the brain can be effectively combined to reconstruct perceptual and subjective images.",
        "authors": [
          "Guohua Shen",
          "Tomoyasu Horikawa",
          "Kei Majima",
          "Yukiyasu Kamitani"
        ]
      },
      {
        "id": 12347,
        "metric": 99096,
        "title": "Could a neuroscientist understand a microprocessor?",
        "url": "https://www.biorxiv.org/content/early/2016/11/14/055624",
        "doi": "10.1101/055624",
        "collection": "neuroscience",
        "first_posted": "26-05-2016",
        "abstract": "There is a popular belief in neuroscience that we are primarily data limited, and that producing large, multimodal, and complex datasets will, with the help of advanced data analysis algorithms, lead to fundamental insights into the way the brain processes information. These datasets do not yet exist, and if they did we would have no way of evaluating whether or not the algorithmically-generated insights were sufficient or even correct. To address this, here we take a classical microprocessor as a model organism, and use our ability to perform arbitrary experiments on it to see if popular data analysis methods from neuroscience can elucidate the way it processes information. Microprocessors are among those artificial information processing systems that are both complex and that we understand at all levels, from the overall logical flow, via logical gates, to the dynamics of transistors. We show that the approaches reveal interesting structure in the data but do not meaningfully describe the hierarchy of information processing in the microprocessor. This suggests current analytic approaches in neuroscience may fall short of producing meaningful understanding of neural systems, regardless of the amount of data. Additionally, we argue for scientists using complex non-linear dynamical systems with known ground truth, such as the microprocessor as a validation platform for time-series and structure discovery methods.",
        "authors": [
          "Eric Jonas",
          "Konrad Kording"
        ]
      }
    ]
  }
}
    """
  )

  # Paper details
  paper_details = docmodels.Chapter("Paper details", "Retrieving more detailed information about a single paper.")
  details = paper_details.add_endpoint("Details", "/papers/<id>", "Retrieve data about a single paper and all of its authors")
  details.add_argument("path", "id", "Rxivist paper ID associated with the paper you want ", required=True)
  details.add_example(
    "Paper detail request",
    "",
    "/papers/12345",
    """{
  "id": 12345,
  "doi": "10.1101/350124",
  "biorxiv_url": "https://www.biorxiv.org/content/early/2018/06/19/350124",
  "url": "https://rxivist.org/papers/12345",
  "title": "Reconstructing intelligible speech from the human auditory cortex",
  "abstract": "Auditory stimulus reconstruction is a technique that finds the best approximation of the acoustic stimulus from the population of evoked neural activity. Reconstructing speech from the human auditory cortex creates the possibility of a speech neuroprosthetic to establish a direct communication with the brain and has been shown to be possible in both overt and covert conditions. However, the low quality of the reconstructed speech has severely limited the utility of this method for brain-computer interface (BCI) applications. To advance the state-of-the-art in speech neuroprosthesis, we combined the recent advances in deep learning with the latest innovations in speech synthesis technologies to reconstruct closed-set intelligible speech from the human auditory cortex. We investigated the dependence of reconstruction accuracy on linear and nonlinear regression methods and the acoustic representation that is used as the target of reconstruction, including spectrogram and speech synthesis parameters. In addition, we compared the reconstruction accuracy from low and high neural frequency ranges. Our results show that a deep neural network model that directly estimates the parameters of a speech synthesizer from all neural frequencies achieves the highest subjective and objective scores on a digit recognition task, improving the intelligibility by 65% over the baseline. These results demonstrate the efficacy of deep learning and speech synthesis algorithms for designing the next generation of speech BCI systems, which not only can restore communications for paralyzed patients but also have the potential to transform human-computer interaction technologies.",
  "downloads": 574,
  "authors": [
    {
      "id": 78107,
      "name": "Hassan Akbari"
    },
    {
      "id": 78108,
      "name": "Bahar Khalighinejad"
    },
    {
      "id": 78109,
      "name": "Jose Herrero"
    },
    {
      "id": 78110,
      "name": "Ashesh Mehta"
    },
    {
      "id": 78111,
      "name": "Nima Mesgarani"
    }
  ],
  "ranks": {
    "alltime": {
      "rank": 6712,
      "tie": false
    },
    "ytd": {
      "rank": 1471,
      "tie": false
    },
    "lastmonth": {
      "rank": 553,
      "tie": false
    },
    "category": {
      "category": "alltime",
      "downloads": 0,
      "rank": 553,
      "tie": false
    }
  }
}
    """
  )

  downloads = paper_details.add_endpoint("Download data", "/papers/<id>/downloads", "Retrieve monthly download statistics for a single paper.")
  downloads.add_argument("path", "id", "Rxivist paper ID associated with the download data you want ", required=True)
  downloads.add_example(
    "Paper download data request",
    "",
    "/papers/12345/downloads",
    """{
  "query": {
    "id": 12345
  },
  "results": [
    {
      "month": 6,
      "year": 2018,
      "downloads": 205
    },
    {
      "month": 7,
      "year": 2018,
      "downloads": 153
    },
    {
      "month": 8,
      "year": 2018,
      "downloads": 88
    },
    {
      "month": 9,
      "year": 2018,
      "downloads": 118
    },
    {
      "month": 10,
      "year": 2018,
      "downloads": 10
    }
  ]
}
    """
  )


  # Author details
  author_details = docmodels.Chapter("Author details", "Retrieving more detailed information about a single author.")
  details = author_details.add_endpoint("Details", "/authors/<id>", "Retrieve data about a single author.")
  details.add_argument("path", "id", "Rxivist paper ID associated with the author in question.", required=True)
  details.add_example(
    "Author detail request",
    "",
    "/authors/12345",
    """{
  "id": 12345,
  "name": "Hernán Ramiro Lascano"
}
    """
  )



  docs = docmodels.Documentation("https://rxivist.org/api/v1", [papers, paper_details, author_details])
  return docs

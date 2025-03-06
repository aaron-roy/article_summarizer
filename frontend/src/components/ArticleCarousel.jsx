import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ArticleCarousel.css';

const ArticleCard = ({ article }) => {
  return (
    <div className="article-card">
      <div className="article-header">
        <h2>Article #{article.id}</h2>
        <p className="author">By {article.author_name}</p>
      </div>
      
      <div className="article-body">
        <p>{article.article_summary}</p>
      </div>
      
      <div className="article-metrics">
        <span><i className="fa fa-heart"></i> Likes: {article.likes}</span>
        <span><i className="fa fa-share"></i> Shares: {article.shares}</span>
        <span><i className="fa fa-eye"></i> Views: {article.views}</span>
      </div>
      
      <div className="article-tags">
        {article.tags.map(tag => (
          <span key={tag.id} className="tag">{tag.tag_name}</span>
        ))}
      </div>
    </div>
  );
};

const ArticleCarousel = () => {
  const [articles, setArticles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://localhost:8000/articles/');
        setArticles(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch articles. Please try again later.');
        setLoading(false);
        console.error('Error fetching articles:', err);
      }
    };

    fetchArticles();
  }, []);

  const nextSlide = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === articles.length - 1 ? 0 : prevIndex + 1
    );
  };

  const prevSlide = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? articles.length - 1 : prevIndex - 1
    );
  };

  if (loading) return <div className="loading">Loading articles...</div>;
  if (error) return <div className="error">{error}</div>;
  if (articles.length === 0) return <div>No articles found.</div>;

  return (
    <div className="carousel-container">
      <button className="carousel-button prev" onClick={prevSlide}>
        &lt;
      </button>
      
      <div className="carousel-slide">
        <ArticleCard article={articles[currentIndex]} />
      </div>
      
      <button className="carousel-button next" onClick={nextSlide}>
        &gt;
      </button>
      
      <div className="carousel-indicators">
        {articles.map((_, index) => (
          <span 
            key={index} 
            className={`indicator ${index === currentIndex ? 'active' : ''}`}
            onClick={() => setCurrentIndex(index)}
          />
        ))}
      </div>


    </div>
  );
};

export default ArticleCarousel;
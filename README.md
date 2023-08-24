# googlecripple
  This project consists of two parcers, custom db cursor and index.

  
  
## class Index
  Saves relation between sites and keywords in the dictionary (dict[str, list(tuple(double, Site))]) of format `['keyword'->[(priority_1:float, site]), ... , (priority_n:float, site])]`
  
  ### add_to_index
  Maintains order of sites in index sorted by tf-idf score of a keyword in site.
  ### search_similar
  Computes similarity to each word in index using Levenshtein distance, chooses 5 most similar to our query.
  ### search_by_keyword
  Returns exact match.
  

  
## Parcer 1: class Parcer
This class has 1 property: `self.opened`: bool. It serves as an indicator of whether the current tag has been closed or not.

### parse_request
  Method `parse_request` splits text of request into head and body sections, divides them into separate lines 
  and then sends them into `parse_head` and `parse_body` respectively.
### parse_head
  Uses  `cur_pos` to navigate on a current parsed line, writes down all meta properties of meta tags in the dict,
  this method omits tags other than meta and title. For title tags it writes down only the title text.
### parse_body
  Works in similar manner to `parse_head`, writes down text between tags in body.
### parse_keywords
  Parses keywords based on tf-idf method. Returns 5 most important words



## Parcer 2: class Parcer_bs
This class' object is initialized by tokenizer object, it has field self.soup for storing BeautifulSoup object.
### get_soup
Creates BeautifulSoup object, finds title, h1 and h2 headers, main text(which we summarize using Extractive summarization in class Tokenizer, it can be slow).
### parse_keywords
  Parses keywords based on tf-idf method. Returns 5 most important words. Uses helper class Tokenizer for tokenizing main text and titles.


## class Tokenizer
Is a helper class for extractive summarization and tokenization of website text.


## class Cursor
Extracting "keyword->site" data for existing objects in database on initialization of a new object. Downloads existing sites to the index using method `get_start_state`.
### insert_page
Creates a new Site object for adding into database and index and prints its string representation.

